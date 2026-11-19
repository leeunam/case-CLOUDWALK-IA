export type Audience = 'simulator' | 'staff'

const protocol = 'actioncable-v1-json'
const heartbeatTimeout = 8000

export function subscribeToCase(
  url: string, caseId: string, audience: Audience, refresh: () => void,
  openSocket = (address: string, subprotocol: string) => new WebSocket(address, subprotocol),
) {
  const identifier = JSON.stringify({ channel: 'CaseUpdatesChannel', case_id: caseId, audience })
  let socket: WebSocket | undefined
  let heartbeat: ReturnType<typeof setTimeout> | undefined
  let retry: ReturnType<typeof setTimeout> | undefined
  let delay = 500
  let stopped = false

  function reconnect() {
    if (stopped || retry !== undefined) return
    retry = setTimeout(() => {
      retry = undefined
      connect()
    }, delay)
    delay = Math.min(delay * 2, 10000)
  }

  function stop() {
    stopped = true
    clearTimeout(retry)
    clearTimeout(heartbeat)
    socket?.close()
    socket = undefined
  }

  function connect() {
    let connection: WebSocket
    try {
      connection = openSocket(url, protocol)
    } catch {
      reconnect()
      return
    }
    socket = connection
    let confirmed = false
    const armHeartbeat = () => {
      clearTimeout(heartbeat)
      heartbeat = setTimeout(() => connection.close(), heartbeatTimeout)
    }
    armHeartbeat()
    connection.onclose = () => {
      if (socket !== connection) return
      clearTimeout(heartbeat)
      socket = undefined
      reconnect()
    }
    connection.onerror = () => connection.close()
    connection.onmessage = event => {
      if (stopped || socket !== connection || typeof event.data !== 'string') return
      let frame
      try {
        frame = JSON.parse(event.data)
      } catch {
        return
      }
      if (!frame || typeof frame !== 'object') return
      armHeartbeat()
      if (frame.type === 'welcome') {
        connection.send(JSON.stringify({ command: 'subscribe', identifier }))
      } else if (frame.type === 'disconnect') {
        if (frame.reconnect === false) {
          stop()
          refresh()
        } else connection.close()
      } else if (frame.identifier === identifier) {
        if (frame.type === 'confirm_subscription') {
          confirmed = true
          delay = 500
          refresh()
        } else if (frame.type === 'reject_subscription') {
          stop()
          refresh()
        } else if (confirmed && frame.message?.type === 'case.updated' && frame.message.case_id === caseId) {
          refresh()
        }
      }
    }
  }

  connect()
  return stop
}
