
import { ArrowLeft } from 'lucide-react';
import Button from '../ui/Button';
import DirectionCard from '../compass/DirectionCard';
import { Expandable } from '../compass/Expandable';
import { completeStreetsCopy } from '../../copy/compass';
import type { Poll, PollOption, Vote } from '../../types';

interface PrincipleProposalProps {
  poll: Poll;
  options: PollOption[];
  myVote: Vote | null;
  onVoteSubmit: (optionId: string) => void;
  onChangeAlignmentTo: (optionId: string) => void;
  isSubmitting: boolean;
  onBack: () => void;
  tally?: Array<{ optionId: string; count: number }>;
  totalVotes: number;
}

export default function PrincipleProposal({
  poll,
  options,
  myVote,
  onVoteSubmit,
  onChangeAlignmentTo,
  isSubmitting,
  onBack,
  tally = [],
  totalVotes
}: PrincipleProposalProps) {
  // Debug logging
  console.log('PrincipleProposal rendered with poll ID:', poll.id);
  console.log('Available principle copy keys:', Object.keys(completeStreetsCopy));

  // Get the principle copy based on poll ID
  const principleCopy = completeStreetsCopy;

  console.log('Found principle copy:', !!principleCopy);

  if (!principleCopy) {
    // Fallback to basic display if no structured copy exists
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                onClick={onBack}
                className="text-gray-700 hover:text-gray-900"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Proposals
              </Button>
            </div>

            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{poll.title}</h1>
            <p className="mt-1 text-gray-700">{poll.description}</p>
          </div>

          <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
            <p className="text-gray-700">This principle proposal is being upgraded to the new structured format.</p>
          </div>
        </div>
      </div>
    );
  }

  // Create mock directions for the two options
  const directions = [
    {
      id: options[0]?.id || 'option-1',
      title: options[0]?.text || 'Direction A',
      description: options[0]?.text,
      votes: tally.find(t => t.optionId === options[0]?.id)?.count || 0
    },
    {
      id: options[1]?.id || 'option-2',
      title: options[1]?.text || 'Direction B',
      description: options[1]?.text,
      votes: tally.find(t => t.optionId === options[1]?.id)?.count || 0
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={onBack}
              className="text-gray-700 hover:text-gray-900"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Proposals
            </Button>
          </div>

          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{principleCopy.title}</h1>
          <p className="mt-1 text-gray-700">{principleCopy.framing}</p>
        </div>

        {/* The Question */}
        <section className="mt-6">
          <h2 className="text-lg font-semibold">{principleCopy.questionHeading}</h2>
          <p className="mt-2 whitespace-pre-line text-gray-800">{principleCopy.questionBody}</p>
        </section>

        {/* Direction Options */}
        <section className="mt-6">
          <h2 className="text-lg font-semibold">Choose a direction to align with</h2>

          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <DirectionCard
              title={principleCopy.dir1.title}
              summary={principleCopy.dir1.summary}
              readMoreHeading={principleCopy.dir1.readMoreHeading}
              rationale={principleCopy.dir1.rationale}
              counterHeading={principleCopy.dir1.counterHeading}
              counters={principleCopy.dir1.counters}
              direction={directions[0]}
              aligned={myVote?.option_id === directions[0]?.id}
              onAlign={() => onVoteSubmit(directions[0]?.id)}
              onChangeAlignment={() => onChangeAlignmentTo(directions[0]?.id)}
              isSubmitting={isSubmitting}
              disabled={!!myVote && myVote.option_id !== directions[0]?.id}
            />
            <DirectionCard
              title={principleCopy.dir2.title}
              summary={principleCopy.dir2.summary}
              readMoreHeading={principleCopy.dir2.readMoreHeading}
              rationale={principleCopy.dir2.rationale}
              counterHeading={principleCopy.dir2.counterHeading}
              counters={principleCopy.dir2.counters}
              direction={directions[1]}
              aligned={myVote?.option_id === directions[1]?.id}
              onAlign={() => onVoteSubmit(directions[1]?.id)}
              onChangeAlignment={() => onChangeAlignmentTo(directions[1]?.id)}
              isSubmitting={isSubmitting}
              disabled={!!myVote && myVote.option_id !== directions[1]?.id}
            />
          </div>
        </section>

        {/* Community Alignment */}
        {totalVotes > 0 && (
          <section className="mt-6">
            <h2 className="text-lg font-semibold">Community alignment (so far)</h2>
            <div className="mt-3 p-6 bg-white rounded-xl border border-gray-200">
              <div className="space-y-4">
                {tally.map((item) => {
                  const option = options.find(o => o.id === item.optionId);
                  const percentage = totalVotes > 0 ? Math.round((item.count / totalVotes) * 100) : 0;

                  return (
                    <div key={item.optionId} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{option?.text || 'Unknown'}</span>
                        <span className="text-gray-600">{item.count} votes ({percentage}%)</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
                <div className="text-sm text-gray-600 text-center pt-2">
                  Total: {totalVotes} votes
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Community Examples */}
        <section className="mt-6">
          <h2 className="text-lg font-semibold">{principleCopy.communityExamplesHeading}</h2>
          <div className="mt-3 p-4 bg-blue-50 rounded-xl border border-blue-200">
            <ul className="space-y-2 text-sm text-gray-700">
              {principleCopy.communityExamples.map((example, i) => (
                <li key={i} className="italic">"{example}"</li>
              ))}
            </ul>
          </div>
        </section>

        {/* Background */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold">{principleCopy.backgroundHeading}</h2>
          <p className="mt-2 text-gray-800">{principleCopy.backgroundSummary}</p>
          <Expandable summary="Read more" id="background-more">
            <ul className="list-disc pl-5">
              {principleCopy.backgroundReadMore.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </Expandable>
        </section>

        {/* Meta Info */}
        <section>
          <div className="flex items-center justify-between p-6 bg-gray-50 rounded-xl border border-gray-200">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>Created {new Date(poll.created_at).toLocaleDateString()}</span>
              </div>
              {poll.updated_at && poll.updated_at !== poll.created_at && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>Updated {new Date(poll.updated_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
