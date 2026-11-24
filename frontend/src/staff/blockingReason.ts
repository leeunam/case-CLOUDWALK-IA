import type { StaffCase } from '../api/contract'

const blocks: Record<string, string> = {
  active_capacity: 'O perfil não comporta mais casos ativos.',
  portfolio_limit: 'A carteira atingiu o limite.',
  different_operating_brand: 'O responsável está operando em outra marca.',
  analyst_unavailable: 'O responsável está indisponível para novas atribuições.',
  brand_switch_pending: 'O responsável está preparando a troca de marca.',
  no_eligible_analyst: 'A fila aguarda um analista elegível.',
  no_responsible_analyst: 'O caso aguarda um responsável para retomar o atendimento.',
  no_active_capacity_profile: 'O analista precisa de um perfil de capacidade ativo.',
  no_human_attendant: 'O atendimento precisa de um analista humano habilitado.',
  invalid_input: 'A categoria ou a prioridade recebida pelo canal está fora do catálogo da marca.',
  insufficient_information: 'O relato tem informações insuficientes para concluir a classificação.',
  classifier_disabled: 'A classificação automática está desativada.',
  invalid_classifier_mode: 'A configuração atual impede a classificação automática.',
  invalid_catalog: 'O catálogo da marca contém opções incompatíveis com o classificador.',
  catalog_unavailable: 'O catálogo está sem opções para completar a classificação.',
  catalog_changed: 'O catálogo mudou durante a classificação.',
  worker_lease_expired: 'O prazo de processamento da classificação terminou.',
  missing_classification_text: 'A mensagem do cliente está ausente na classificação.',
  invalid_response: 'O classificador retornou uma resposta inválida.',
  missing_credentials: 'O acesso ao serviço de classificação precisa ser configurado.',
  http_error: 'O serviço de classificação retornou um erro.',
  network_error: 'A conexão com o serviço de classificação falhou.',
  timeout: 'O serviço de classificação excedeu o prazo de resposta.',
  agent_result_timeout: 'O atendente de IA excedeu o prazo de resposta.',
  queue_access_revoked: 'O responsável perdeu acesso à fila.',
}

export function blockingMessage(reason: string, status: StaffCase['status'], integration: StaffCase['integration_status']) {
  const explanation = Object.hasOwn(blocks, reason) ? blocks[reason] : undefined
  if (status === 'classification_review') {
    return [explanation, 'A supervisão precisa revisar a categoria e a prioridade.'].filter(Boolean).join(' ')
  }
  if (integration === 'failed') {
    const failure = explanation ?? (reason.startsWith('bridge_')
      ? 'A entrega do pedido ao atendente de IA falhou.' : 'A integração com o atendente de IA falhou.')
    return failure + ' A supervisão pode tentar novamente ou encaminhar o caso para atendimento humano.'
  }
  return explanation ?? 'O atendimento está bloqueado. A supervisão pode consultar o motivo no registro do caso.'
}
