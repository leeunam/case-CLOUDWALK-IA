import type { ActorType, CaseStatus, Category, ChannelType, Priority } from './contract'

export const channelLabels: Record<ChannelType, string> = {
  chat: 'Chat',
  whatsapp: 'WhatsApp',
  email: 'E-mail',
}

export const caseLabels: Record<CaseStatus, string> = {
  classification_pending: 'Aguardando classificação',
  classification_review: 'Em revisão',
  ai_active: 'Em atendimento',
  waiting_human: 'Aguardando equipe',
  human_active: 'Com a equipe de suporte',
  waiting_customer: 'Aguardando você',
  waiting_resumption: 'Aguardando retomada',
  resolved: 'Resolvido',
}

export const authorLabels: Record<ActorType, string> = {
  customer: 'Você',
  ai: 'Atendente de IA',
  human: 'Equipe de suporte',
  supervisor: 'Supervisão',
  system: 'Sistema',
}

export const categoryLabels: Record<Category, string> = {
  pix: 'Pix',
  payouts: 'Repasses',
  terminal: 'Maquininha',
}

export const priorityLabels: Record<Priority, string> = {
  basic: 'Básica',
  intermediate: 'Intermediária',
  advanced: 'Avançada',
  urgent: 'Urgente',
}

export const channelExamples = {
  chat: { text: 'Qual é o prazo de confirmação de um Pix?', category: 'pix', priority: 'basic' },
  whatsapp: {
    text: 'O visor da maquininha está apagado desde a troca de bateria.',
    category: 'terminal',
    priority: 'advanced',
  },
  email: { text: 'Onde consigo consultar a previsão do meu repasse?', category: 'payouts', priority: 'intermediate' },
} satisfies Record<ChannelType, { text: string; category: Category; priority: Priority }>

const timestampFormatter = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' })

export function formatTimestamp(timestamp: string) {
  return timestampFormatter.format(new Date(timestamp))
}
