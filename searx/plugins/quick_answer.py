# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, missing-class-docstring
import json
from datetime import datetime

from flask_babel import gettext

from searx.plugins import Plugin, PluginInfo


class SXNGPlugin(Plugin):
    id = "quick_answer"
    default_on = False

    def __init__(self):
        super().__init__()

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Quick Answer"),
            description=gettext("Use search results to obtain cited answers from LLMs by appending '?' to queries"),
            examples=["Linear congruential generator?"],
            preference_section="general/quick_answer",
        )

    def get_sys_prompt(self):
        now = datetime.now()
        return f"""
        The current date is {now:%Y-%m-%d}

        You ALWAYS follow these guidelines when writing your response:
        - Use markdown formatting to enhance clarity and readability of your response.
        - If you need to include mathematical expressions, use LaTeX to format them properly. Only use LaTeX when necessary for math.
        - Delimit inline mathematical expressions with '$', for example: $y = mx + b$.
        - Delimit block mathematical expressions with '$$', for example: $$F = ma$$.
        - If you need to write code or program commands, format them as markdown code blocks.
        - For all other output, use plain text formatting unless the user specifically requests otherwise.
        - DO NOT include headers which only describe or rephrase the query before beginning your response.
        - DO NOT include URLs or links in your response.
        - ALWAYS enclose currency and price values in '**', for example: **$5.99**, to ensure they are formatted correctly.

        The relevant available information is contained within the <information></information> tags. When a user asks a question, perform the following tasks:
        0. Examine the available information and assess whether you can answer the question based on it, even if the answer is not explicitly stated. For example, if the question asks about a specific feature of a product and the available information discusses the product's features without mentioning the specific feature, you can infer that the product likely does not have that feature.
        1. Use the available information to inform your answer.
        2. When answering questions, provide inline citation references by putting their citation index delimited by 【 and 】 at end of sentence, example: This is a claim【1】."
        3. If you need to cite multiple pieces of information inline, use separate 【 and 】 for each citation, example: "This is a claim【1】【2】."
        4. Use citations most relevant to the query to augment your answer with informative supportive resources; do not create unhelpful, extended chains of citations.
        5. DO NOT list URLs/links of the citation source or an aggregate list of citations at the end of the response. They would be automatically added by the system based on citation indices.
        6. DO NOT provide inline citations inside or around code blocks, as they break formatting of output, only provide them to augment plaintext.
        7. DO NOT use markdown to format your citations, always provide them in plaintext.

        A few guidelines for you when answering questions:
        - Highlight relevant entities/phrases with **, for example: "**Neil Armstrong** is known as the first person to land on the moon." (Do not apply this guideline to citations or in code blocks.)
        - DO NOT talk about how you based your answer on the information provided to you as it may confuse the user.
        - Don't copy-paste the information from the available information directly. Paraphrase the information in your own words.
        - Even if the information is in another format, your output MUST follow the guidelines. for example: output O₁ instead of O<sub>1</sub>, output R⁷ instead of R<sup>7</sup>, etc.
        - Be concise and informative in your answers.
        """

    def format_sources(self, sources):
        ret = "<available_information>\n"
        for pos, source in enumerate(sources):
            ret += "<datum>\n"
            ret += f'<citation index="{pos}">\n'
            ret += f"<source>\n{source.get('url', '')}\n</source>\n"
            ret += f"<title>\n{source.get('title', '')}\n</title>\n"
            ret += f"<content>\n{source.get('content', '')}\n</content>\n"
            ret += "</datum>\n"

        return ret + "</available_information>"

    def post_search(self, request, search):
        query = search.search_query
        if query.pageno > 1 or not query.query.endswith("?"):
            return

        token = request.preferences.get_value("quick_answer_token")
        if not token:
            return

        model = request.preferences.get_value("quick_answer_model")
        providers = request.preferences.get_value("quick_answer_providers")
        if providers:
            providers = [provider.strip() for provider in providers.split(",")]

        sources = search.result_container.get_ordered_results()
        formatted_sources = self.format_sources(sources)
        user = formatted_sources + f"\n\nUser query: {query.query}"
        system = self.get_sys_prompt()

        reference_map = {str(i): (source.get("url"), source.get("title")) for i, source in enumerate(sources)}

        search.result_container.infoboxes.append(
            {
                "infobox": "Quick Answer",
                "id": "quick_answer",
                "content": f"""
                <script>
                    window.systemPrompt = {json.dumps(system)};
                    window.userPrompt = {json.dumps(user)};
                    window.userToken = {json.dumps(token)};
                    window.userModel = {json.dumps(model)};
                    window.userProviders = {json.dumps(providers)};
                    window.referenceMap = {json.dumps(reference_map)};
                </script>
            """,
            }
        )

    name = gettext("Quick Answer")
    description = gettext("Use search results to obtain cited answers from LLMs by appending '?' to queries")
    default_on = False
    preference_section = "general"
