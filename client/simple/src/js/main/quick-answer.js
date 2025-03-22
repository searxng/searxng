import { marked } from "../../../node_modules/marked/lib/marked.esm.js";
import renderMathInElement from "../../../node_modules/katex/dist/contrib/auto-render.js";

document.addEventListener("DOMContentLoaded", () => {
  if (typeof window.referenceMap === "undefined") {
    console.error("referenceMap is not defined");
    return;
  }

  marked.setOptions({
    gfm: true,
    breaks: true,
    highlight: function (code, language) {
      if (language) {
        return (
          '<pre><code class="language-' +
          language +
          '">' +
          code.replace(
            /[&<>'"]/g,
            (c) =>
              ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                "'": "&#39;",
                '"': "&quot;",
              })[c],
          ) +
          "</code></pre>"
        );
      }
      return code;
    },
  });

  const renderer = new marked.Renderer();
  renderer.link = (token) => {
    const href = token.href;
    const title = token.title || "";
    const text = token.text;
    return `<a href="${href}" title="${title}" rel="noreferrer">${text}</a>`;
  };
  marked.use({ renderer });

  // Custom math handling; we roll our own because LLMs are inconsistent(!)
  const mathExtension = {
    name: "math",
    level: "block",
    start(src) {
      return src.match(/\$\$/)?.index;
    },
    tokenizer(src) {
      const rule = /^\$\$([\s\S]+?)\$\$/;
      const match = rule.exec(src);
      if (match) {
        return {
          type: "math",
          raw: match[0],
          text: match[1].trim(),
        };
      }
    },
    renderer(token) {
      return `$$${token.text}$$`;
    },
  };

  const inlineMathExtension = {
    name: "inlineMath",
    level: "inline",
    start(src) {
      return src.match(/\$/)?.index;
    },
    tokenizer(src) {
      const rule = /^\$([^$\n]+?)\$/;
      const match = rule.exec(src);
      if (match) {
        return {
          type: "inlineMath",
          raw: match[0],
          text: match[1].trim(),
        };
      }
    },
    renderer(token) {
      return `$${token.text}$`;
    },
  };

  marked.use({ extensions: [mathExtension, inlineMathExtension] });

  // Answer
  const qa = document.querySelector(".infobox p");
  if (!qa) {
    console.error("Quick answer container not found");
    return;
  }
  qa.id = "quick-answer";
  qa.className = "markdown-content";

  // References
  const refContainer = document.createElement("div");
  refContainer.className = "references";
  const refHeading = document.createElement("h4");
  refHeading.textContent = "References";
  refContainer.appendChild(refHeading);
  const refList = document.createElement("ol");
  refContainer.appendChild(refList);
  qa.after(refContainer);

  let accumulatedText = "";
  let lastProcessedLength = 0;
  let references = {};
  let referenceCounter = 1;
  let referenceMap = window.referenceMap;

  function escapeHtml(unsafe) {
    return unsafe.replace(/[&<>"']/g, function (m) {
      switch (m) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      case "'":
        return "&#039;";
      default:
        return m;
      }
    });
  }

  function replaceCitations(text) {
    // First pass: replace citations with temporary markers to be replaced by actual spaces in the second pass
    // LLMs do not consistently follow prompted formatting, and inline citations *need* to be space-delimited
    let processedText = text.replace(
      /【(\d+)】/g,
      (match, citationIndex, offset) => {
        const isFollowedByCitation = text
          .slice(offset + match.length)
          .match(/^【\d+】/);
        const source = referenceMap[citationIndex];

        if (source) {
          const [url, title] = source;
          let refNumber = references[citationIndex];
          const escapedTitle = escapeHtml(title);

          if (!refNumber) {
            const refItem = document.createElement("li");
            const refLink = document.createElement("a");
            refLink.href = url;
            refLink.textContent = title;
            refLink.rel = "noreferrer";
            refItem.appendChild(refLink);
            refList.appendChild(refItem);
            references[citationIndex] = referenceCounter;
            refNumber = referenceCounter;
            referenceCounter += 1;
          }

          // Add look-ahead marker |||CITATION_SPACE||| if followed by another citation
          return `<a href="${url}" class="inline-reference" title="${escapedTitle}">${refNumber}</a>${
            isFollowedByCitation ? "|||CITATION_SPACE|||" : ""
          }`;
        }
        return match;
      },
    );

    // Second pass: replace temporary markers with spaces
    return processedText.replace(/\|\|\|CITATION_SPACE\|\|\|/g, " ");
  }

  fetch("/quick_answer", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      system: window.systemPrompt,
      user: window.userPrompt,
      token: window.userToken,
      model: window.userModel,
      providers: window.userProviders,
    }),
  })
    .then((response) => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      function processMarkdownChunk(text) {
        accumulatedText += text;

        const markdownElements = {
          codeBlock: { start: "```", end: "```" },
          bold: { start: "**", end: "**" },
          italic: { start: "_", end: "_" },
          link: { start: "[", end: ")" },
          mathDisplay: { start: "$$", end: "$$" },
          mathInline: { start: "$", end: "$" },
        };

        let processUpTo = accumulatedText.length;

        // Find last complete element
        for (const element of Object.values(markdownElements)) {
          const lastStart = accumulatedText.lastIndexOf(element.start);
          if (lastStart > lastProcessedLength) {
            const nextEnd = accumulatedText.indexOf(
              element.end,
              lastStart + element.start.length,
            );
            if (nextEnd === -1) {
              processUpTo = Math.min(processUpTo, lastStart);
            }
          }
        }

        // Process complete portion
        if (processUpTo > lastProcessedLength) {
          const processedText = replaceCitations(
            accumulatedText.substring(0, processUpTo),
          );
          qa.innerHTML = marked.parse(processedText);

          renderMathInElement(qa, {
            delimiters: [
              { left: "$$", right: "$$", display: true },
              { left: "$", right: "$", display: false },
            ],
            throwOnError: false,
          });

          lastProcessedLength = processUpTo;
        }
      }

      function readStream() {
        reader
          .read()
          .then(({ done, value }) => {
            if (done) {
              // Process any remaining text
              if (accumulatedText.length > lastProcessedLength) {
                const processedText = replaceCitations(accumulatedText);
                qa.innerHTML = marked.parse(processedText);
                renderMathInElement(qa, {
                  delimiters: [
                    { left: "$$", right: "$$", display: true },
                    { left: "$", right: "$", display: false },
                  ],
                  throwOnError: false,
                });
              }
              return;
            }

            const text = decoder.decode(value, { stream: true });
            processMarkdownChunk(text);

            // Scroll to bottom of the div to show new content
            qa.scrollTop = qa.scrollHeight;

            // Continue reading
            readStream();
          })
          .catch((error) => console.error("Error:", error));
      }
      readStream();
    })
    .catch((error) => {
      console.error("Error:", error);
      qa.innerHTML = marked.parse(`**Error**: ${error.message}`);
    });
});
