import { motion } from 'framer-motion';

type TallyItem = {
  id: string;
  title: string;
  count: number;
};

type Props = {
  items: TallyItem[];
  total: number;
};

export default function CompassTally({ items, total }: Props) {
  if (total === 0) {
    return (
      <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
        <p className="text-gray-700">No alignments yet. Be the first to choose a direction.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item) => {
        const percentage = total > 0 ? (item.count / total) * 100 : 0;
        
        return (
          <div key={item.id} className="space-y-2" data-testid={`tally-${item.id}`}>
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900">{item.title}</span>
              <div className="text-sm text-gray-600">
                <span className="font-medium">{item.count}</span>
                <span className="mx-1">•</span>
                <span>{percentage.toFixed(1)}%</span>
              </div>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <motion.div
                className="h-full bg-blue-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                role="progressbar"
                aria-valuenow={item.count}
                aria-valuemin={0}
                aria-valuemax={total}
                aria-label={`${item.title}: ${item.count} out of ${total} votes (${percentage.toFixed(1)}%)`}
              />
            </div>
          </div>
        );
      })}
      
      <div className="text-sm text-gray-600 text-center pt-2">
        <span className="font-medium">{total}</span> total alignments
      </div>
    </div>
  );
}
