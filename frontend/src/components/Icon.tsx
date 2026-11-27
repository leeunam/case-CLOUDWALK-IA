const paths = {
  inbox: 'M3 13l3-8h12l3 8v6H3z M3 13h5l2 3h4l2-3h5',
  review: 'M5 4h10l4 4v12H5z M14 4v5h5 M9 14h6',
  alert: 'M12 3 2 20h20z M12 9v4 M12 16v.5',
  settings: 'M4 7h6m4 0h6 M4 17h10m4 0h2 M10 4v6 M16 14v6',
  chat: 'M4 4h16v12H9l-5 4z',
  email: 'M3 5h18v14H3z M3 6l9 7 9-7',
  whatsapp: 'M7 20l-4 1 1-5a9 9 0 1 1 3 4z M8 8c0 4 3 7 7 8l2-2-3-2-1 1c-1-.5-2-1.5-2.5-2.5l1-1-2-3z',
  refresh: 'M20 10a8 8 0 0 0-14-4L3 9 M3 4v5h5 M4 14a8 8 0 0 0 14 4l3-3 M21 20v-5h-5',
  list: 'M4 6h2m3 0h11 M4 12h2m3 0h11 M4 18h2m3 0h11',
  context: 'M3 4h18v16H3z M14 4v16',
  plus: 'M12 5v14 M5 12h14',
  filter: 'M3 5h18l-7 8v5l-4 2v-7z',
  logout: 'M10 4H4v16h6 M8 12h13m-5-5 5 5-5 5',
  pulse: 'M2 12h5l3-7 4 14 3-7h5',
  key: 'M5 10h14v10H5z M8 10V7a4 4 0 0 1 8 0v3 M12 14v2',
  history: 'M3 5v5h5 M4 9a8 8 0 1 1 0 7 M12 8v5l3 2',
  arrow: 'M5 12h14m-5-5 5 5-5 5',
}
export type IconName = keyof typeof paths
export function Icon({ name }: { name: IconName }) {
  return <svg aria-hidden="true" focusable="false" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round">
    <path d={paths[name]} />
  </svg>
}
