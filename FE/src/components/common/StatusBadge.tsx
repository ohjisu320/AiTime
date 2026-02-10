interface StatusBadgeProps {
  status: string;
  label?: string;
}

export default function StatusBadge({ status, label }: StatusBadgeProps) {
  let styleClass = "bg-gray-100 text-gray-600";

  switch (status) {
    case "COMPLETED":
    case "REGISTERED":
      styleClass = "bg-blue-50 text-[#5A55D6]";
      break;
    case "IN_PROGRESS":
    case "ISSUED":
      styleClass = "bg-orange-50 text-orange-600";
      break;
    case "REVOKED":
    case "FAILED":
      styleClass = "bg-red-50 text-red-600";
      break;
  }

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-bold ${styleClass}`}>
      {label || status}
    </span>
  );
}
