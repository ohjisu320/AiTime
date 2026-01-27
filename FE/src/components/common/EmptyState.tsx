interface EmptyStateProps {
  date?: string;
  message: string;
}

export default function EmptyState({ date, message }: EmptyStateProps) {
  return (
    <div className="py-20 text-center flex flex-col items-center justify-center text-gray-400">
      {date && <div className="text-lg font-bold mb-1">{date}</div>}
      <p>{message}</p>
    </div>
  );
}
