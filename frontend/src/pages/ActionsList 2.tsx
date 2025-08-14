import ProposalGrid from '../components/ProposalGrid';

export default function ActionsList() {
  return (
    <ProposalGrid
      title="Actions"
      decisionType="level_b"
      emptyTitle="No actions yet"
      emptySubtitle="Be the first to propose a concrete action for your community."
      ctaLabel="Propose an Action"
      pageDescription="Concrete choices we can act on now."
    />
  );
}
