const { req } = require('../../utils/request.js')
const { STATUS_LABEL, STATUS_COLOR, fmtApptTime, todayStr } = require('../../utils/util.js')

function nextAction(status) {
  switch (status) {
    case 'BOOKED': return { label: '确认', event: 'CONFIRM' }
    case 'CONFIRMED': return { label: '标记到诊', event: 'PATIENT_ARRIVE' }
    case 'ARRIVED': return { label: '开始诊疗', event: 'START_TREATMENT' }
    case 'IN_PROGRESS': return { label: '完成', event: 'FINISH' }
    default: return null
  }
}

Page({
  data: { list: [], loading: true, date: '' },

  onShow() {
    this.setData({ date: todayStr() })
    this.load()
  },

  load() {
    this.setData({ loading: true })
    req('/api/appointments?date=' + this.data.date).then((list) => {
      const items = (list || []).map((a) => {
        const act = nextAction(a.status)
        return {
          appointment_id: a.appointment_id,
          patient_name: a.patient_name || ('患者#' + a.patient_id),
          chair_code: a.chair_code || ('椅#' + a.chair_id),
          time: fmtApptTime(a.start_time),
          statusLabel: STATUS_LABEL[a.status] || a.status,
          color: STATUS_COLOR[a.status] || '#999',
          actionLabel: act ? act.label : '',
          actionEvent: act ? act.event : ''
        }
      })
      this.setData({ list: items, loading: false })
    }).catch(() => {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    })
  },

  advance(e) {
    const id = e.currentTarget.dataset.id
    const ev = e.currentTarget.dataset.event
    req('/api/appointments/' + id + '/event', 'POST', { event: ev })
      .then(() => { wx.showToast({ title: '已更新', icon: 'success' }); this.load() })
      .catch((err) => wx.showModal({ title: '操作失败', content: err.message || '请重试', showCancel: false }))
  }
})
