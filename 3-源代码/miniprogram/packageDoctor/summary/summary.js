const { req } = require('../../utils/request.js')
const { STATUS_LABEL, STATUS_COLOR, fmtApptTime, todayStr } = require('../../utils/util.js')

Page({
  data: { list: [], loading: true, date: '' },

  onShow() {
    this.setData({ date: todayStr() })
    this.load()
  },

  load() {
    this.setData({ loading: true })
    req('/api/appointments?date=' + this.data.date).then((list) => {
      const items = (list || []).map((a) => ({
        appointment_id: a.appointment_id,
        patient_name: a.patient_name || ('患者#' + a.patient_id),
        chair_code: a.chair_code || ('椅#' + a.chair_id),
        time: fmtApptTime(a.start_time),
        statusLabel: STATUS_LABEL[a.status] || a.status,
        color: STATUS_COLOR[a.status] || '#999'
      }))
      this.setData({ list: items, loading: false })
    }).catch(() => {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    })
  }
})
