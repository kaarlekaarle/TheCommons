

export default function LiveIndicator() {
  return (
    <div 
      className="flex items-center gap-2 text-xs text-muted"
      title="Live connection"
    >
      <div className="relative">
        <div className="w-2 h-2 bg-green-500 rounded-full" />
        <div className="absolute inset-0 w-2 h-2 bg-green-500 rounded-full animate-pulse opacity-75" />
      </div>
      <span>Live</span>
    </div>
  );
}
