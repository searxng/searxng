// Closes issues and prs whose authors/agents don't accept the ai policy
// https://github.com/searxng/searxng/blob/master/AI_POLICY.rst

module.exports = async ({ github, context }) => {
  const item = context.payload.pull_request || context.payload.issue;
  const body = item.body || '';
  const kind = context.payload.pull_request ? 'pull request' : 'issue';

  // https://github.com/searxng/searxng/pull/6476#discussion_r3683782481
  const hasBox = /\[[Xx]\].*AI Policy/.test(body);
  const hasRef = /\[AI Policy\]:\s*https:\/\/github\.com\/searxng\/searxng\/.*AI_POLICY/.test(body);
  if (hasBox && hasRef) {
    return;
  }

  const { owner, repo } = context.repo;
  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: item.number,
    body:
      'Hello! Thank you for your contribution.\n\n' +
      `Unfortunately your ${kind} was closed as the AI Policy has not been accepted.\n\n` +
      `Please open a new ${kind} after confirming your contribution aligns with our AI Policy.`,
  });
  await github.rest.issues.addLabels({
    owner,
    repo,
    issue_number: item.number,
    labels: ['invalid:slop'],
  });
  await github.rest.issues.update({
    owner,
    repo,
    issue_number: item.number,
    state: 'closed',
    state_reason: 'not_planned',
  });
};
