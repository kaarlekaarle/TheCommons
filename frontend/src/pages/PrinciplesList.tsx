import ProposalGrid from '../components/ProposalGrid';

export default function PrinciplesList() {
  return (
    <ProposalGrid
      title="Principles"
      decisionType="level_a"
      emptyTitle="No principles yet"
      emptySubtitle="Be the first to propose a long-term direction for your community."
      ctaLabel="Propose a Principle"
      pageDescription="Shared north stars for our community (changed rarely)."
    />
  );
}
