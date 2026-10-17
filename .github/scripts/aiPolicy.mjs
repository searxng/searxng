// @ts-check
// Closes issues and prs whose authors/agents don't accept the ai policy
// https://github.com/searxng/searxng/blob/master/AI_POLICY.rst

const boxCocRegex = /\[\s*[Xx]\s*\].*AI Policy/;
const refCocRegex = /\[AI Policy\](?::\s*|\()https:\/\/github\.com\/searxng\/searxng\/.*AI_POLICY/;

export default async ({ github, context }) => {
    const item = context.payload.issue ?? context.payload.pull_request;
    if (!item?.body) {
        return;
    }

    if (boxCocRegex.test(item.body) && refCocRegex.test(item.body)) {
        return;
    }

    const type = context.payload.issue ? "issue" : "pull request";

    await github.rest.issues.createComment({
        issue_number: item.number,
        body: `Hello! Thank you for your contribution.

Unfortunately your ${type} was closed as the AI Policy has not been accepted.
Please open a new ${type} after confirming your contribution aligns with our AI Policy.`,
        ...context.repo
    });

    await github.rest.issues.addLabels({
        issue_number: item.number,
        labels: ["invalid:slop"],
        ...context.repo
    });

    await github.rest.issues.update({
        issue_number: item.number,
        state: "closed",
        state_reason: "not_planned",
        ...context.repo
    });
};
