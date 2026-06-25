interface NaxelyMarkProps {
  size?: number;
  color?: string;
  className?: string;
}

export function NaxelyMark({ size = 24, color = '#D97A34', className }: NaxelyMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <rect x="1" y="16" width="4" height="7" rx="1" fill={color} />
      <rect x="7" y="11" width="4" height="12" rx="1" fill={color} />
      <rect x="13" y="6" width="4" height="17" rx="1" fill={color} />
      <rect x="19" y="1" width="4" height="22" rx="1" fill={color} />
    </svg>
  )
}
