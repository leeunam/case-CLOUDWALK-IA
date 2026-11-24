type Navigation = { caseId: string | null; showHistory: boolean }
type Action =
  | { type: 'open'; caseId: string | null }
  | { type: 'showHistory'; visible: boolean }
  | { type: 'receipt'; submittedFrom: string | null; caseId: string }

export function navigate(state: Navigation, action: Action): Navigation {
  switch (action.type) {
    case 'open':
      return { caseId: action.caseId, showHistory: false }
    case 'showHistory':
      return { ...state, showHistory: action.visible }
    case 'receipt':
      if (state.caseId !== action.submittedFrom || state.caseId === action.caseId) return state
      return { ...state, caseId: action.caseId }
  }
}

export function focusAfterNavigation(trigger: Pick<HTMLElement, 'getClientRects'>, heading: Pick<HTMLElement, 'focus'> | null) {
  if (!trigger.getClientRects().length) heading?.focus()
}
