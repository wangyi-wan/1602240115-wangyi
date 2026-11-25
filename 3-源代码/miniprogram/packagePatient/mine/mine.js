const { req } = require('../../utils/request.js')
const { STATUS_LABEL, STATUS_COLOR, fmtApptTime } = require('../../utils/util.js')

Page({
  data: { list: [], loading: true },

  onShow() { this.load() },

  load() {
    this.setData({ loading: true })
    req('/api/appointments').then((list) => {
      const items = (list || []).map((a) => ({
        appointment_id: a.appointment_id,
        patient_name: a.patient_name || ('患者#' + a.patient_id),
        chair_code: a.chair_code || ('椅#' + a.chair_id),
        time: fmtApptTime(a.start_time),
        statusLabel: STATUS_LABEL[a.status] || a.status,
        color: STATUS_COLOR[a.status] || '#999',
        canCancel: a.status === 'BOOKED'
      }))
      this.setData({ list: items, loading: false })
    }).catch(() => {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    })
  },

  cancel(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '取消预约',
      content: '确定要取消这条预约吗？',
      success: (r) => {
        if (!r.confirm) return
        req('/api/appointments/' + id + '/event', 'POST', { event: 'PATIENT_CANCEL' })
          .then(() => { wx.showToast({ title: '已取消', icon: 'success' }); this.load() })
          .catch((err) => wx.showModal({ title: '取消失败', content: err.message || '请重试', showCancel: false }))
      }
    })
  }
})
