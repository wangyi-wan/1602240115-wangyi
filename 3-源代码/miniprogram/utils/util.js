const formatTime = date => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('/')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

const formatNumber = n => {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

// 预约状态 → 中文标签（与后端 t_appointment.status 一一对应）
const STATUS_LABEL = {
  BOOKED: '已预约',
  CONFIRMED: '已确认',
  ARRIVED: '已到诊',
  IN_PROGRESS: '诊疗中',
  DONE: '已完成',
  CANCELLED: '已取消',
  NO_SHOW: '失约'
}

// 把后端返回的 ISO 时间 "2026-11-03T08:30:00" 变成 "11-03 08:30"
const fmtApptTime = iso => {
  if (!iso) return ''
  const s = String(iso).replace('T', ' ')
  const m = s.match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/)
  if (!m) return s
  return `${m[2]}-${m[3]} ${m[4]}:${m[5]}`
}

// 今天的本地日期 "YYYY-MM-DD"
const todayStr = () => {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

// 状态 → 标签颜色（红=进行中/待处理，灰=终态）
const STATUS_COLOR = {
  BOOKED: '#1677ff',
  CONFIRMED: '#722ed1',
  ARRIVED: '#fa8c16',
  IN_PROGRESS: '#eb2f96',
  DONE: '#52c41a',
  CANCELLED: '#999999',
  NO_SHOW: '#f5222d'
}

module.exports = {
  formatTime,
  STATUS_LABEL,
  fmtApptTime,
  todayStr,
  STATUS_COLOR
}
