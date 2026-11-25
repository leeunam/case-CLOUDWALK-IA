import type { Session, StaffCase } from './contract'

export function canHandle(session: Session, detail: StaffCase) {
  return session.user?.role === 'analyst' &&
    detail.status === 'human_active' &&
    detail.assignee?.type === 'human' &&
    detail.assignee.id === session.user.attendant_id &&
    session.user.brand_ids.includes(detail.brand_id) &&
    detail.brand_id === session.operation?.active_brand_id
}
