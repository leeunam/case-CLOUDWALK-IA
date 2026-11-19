import { caseLabels } from '../simulator/presentation'

export const staffCaseLabels = {
  ...caseLabels,
  human_active: 'Em atendimento humano',
  waiting_customer: 'Aguardando cliente',
  waiting_human: 'Aguardando atribuição',
}
