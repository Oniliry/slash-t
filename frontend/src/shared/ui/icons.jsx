const commonProps = {
  width: 22,
  height: 22,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  className: 'tab-bar__icon',
  'aria-hidden': 'true',
}

export function HomeIcon() {
  return (
    <svg {...commonProps}>
      <path d="M4 11.5 12 4l8 7.5" />
      <path d="M6 10v9a1 1 0 0 0 1 1h3v-5a2 2 0 0 1 4 0v5h3a1 1 0 0 0 1-1v-9" />
    </svg>
  )
}

export function ReceiptIcon() {
  return (
    <svg {...commonProps}>
      <path d="M6 3h12v17.5l-2.5-1.5-2 1.5-2-1.5-2 1.5-2-1.5L6 20.5Z" />
      <path d="M8.5 8h7" />
      <path d="M8.5 11.5h7" />
      <path d="M8.5 15h4.5" />
    </svg>
  )
}

export function CushionIcon() {
  return (
    <svg {...commonProps}>
      <path d="M12 3.5 19 6v5.5c0 4.2-2.8 7.4-7 9-4.2-1.6-7-4.8-7-9V6l7-2.5Z" />
      <circle cx="12" cy="11" r="2.5" />
      <path d="M12 9.5v3" />
      <path d="M10.5 11h3" />
    </svg>
  )
}

export function FamilyIcon() {
  return (
    <svg {...commonProps}>
      <circle cx="7.5" cy="7" r="2.3" />
      <circle cx="16.5" cy="7" r="2.3" />
      <path d="M3 19c0-3 2-5.2 4.5-5.2S12 16 12 19" />
      <path d="M12 19c0-3 2-5.2 4.5-5.2S21 16 21 19" />
      <path d="M10.3 15.3h3.4" />
    </svg>
  )
}

export function ProfileIcon() {
  return (
    <svg {...commonProps}>
      <circle cx="12" cy="8" r="3.4" />
      <path d="M5 20c.8-3.5 3.6-5.5 7-5.5s6.2 2 7 5.5" />
    </svg>
  )
}

export function LogoutIcon() {
  return (
    <svg {...commonProps}>
      <path d="M14 5H6.5A1.5 1.5 0 0 0 5 6.5v11A1.5 1.5 0 0 0 6.5 19H14" />
      <path d="M11 12h8" />
      <path d="m16 8 4 4-4 4" />
    </svg>
  )
}

export function EditIcon() {
  return (
    <svg {...commonProps}>
      <path d="m14.5 5.5 4 4" />
      <path d="m5 19 1.2-4.3L15.8 5a1.7 1.7 0 0 1 2.4 0l.8.8a1.7 1.7 0 0 1 0 2.4l-9.7 9.6Z" />
      <path d="M5 19h4" />
    </svg>
  )
}
