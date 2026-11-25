const { req } = require('../../utils/request.js')
const { STATUS_LABEL, STATUS_COLOR, fmtApptTime, todayStr } = require('../../utils/util.js')

function nextAction(status) {
  switch (status) {
    case 'BOOKED': return { label: '确认预约', event: 'CONFIRM' }
    case 'CONFIRMED': return { label: '标记到诊', event: 'PATIENT_ARRIVE' }
    case 'ARRIVED': return { label: '开始诊疗', event: 'START_TREATMENT' }
    case 'IN_PROGRESS': return { label: '完成诊疗', event: 'FINISH' }
    default: return null
  }
}

Page({
  data: {
    mode: 'list',          // list = 选患者；detail = 制定方案
    list: [], detail: null, note: '', loading: true, date: '', id: ''
  },

  onLoad(options) {
    if (options && options.id) {
      this.setData({ mode: 'detail', id: options.id })
    } else {
      this.setData({ mode: 'list', date: todayStr() })
    }
  },

  onShow() {
    if (this.data.mode === 'detail') this.loadDetail()
    else this.loadList()
  },

  loadList() {
    this.setData({ loading: true })
    req('/api/appointments?date=' + this.data.date).then((list) => {
      const items = (list || []).map((a) => ({
        appointment_id: a.appointment_id,
        patient_name: a.patient_name || ('患者#' + a.patient_id),
        time: fmtApptTime(a.start_time),
        statusLabel: STATUS_LABEL[a.status] || a.status,
        color: STATUS_COLOR[a.status] || '#999'
      }))
      this.setData({ list: items, loading: false })
    }).catch(() => { wx.showToast({ title: '加载失败', icon: 'none' }); this.setData({ loading: false }) })
  },

  openDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/packageDoctor/plan/plan?id=' + id })
  },

  loadDetail() {
    this.setData({ loading: true })
    req('/api/appointments').then((list) => {
      const a = (list || []).find((x) => String(x.appointment_id) === String(this.data.id))
      if (!a) { wx.showToast({ title: '未找到', icon: 'none' }); this.setData({ loading: false }); return }
      const act = nextAction(a.status)
      const stored = wx.getStorageSync('plan_' + a.appointment_id) || ''
      this.setData({
        detail: {
          appointment_id: a.appointment_id,
          patient_name: a.patient_name || ('患者#' + a.patient_id),
          chair_code: a.chair_code || ('椅#' + a.chair_id),
          time: fmtApptTime(a.start_time),
          statusLabel: STATUS_LABEL[a.status] || a.status,
          color: STATUS_COLOR[a.status] || '#999',
          status: a.status,
          actionLabel: act ? act.label : '',
          actionEvent: act ? act.event : ''
        },
        note: stored,
        loading: false
      })
    }).catch(() => { wx.showToast({ title: '加载失败', icon: 'none' }); this.setData({ loading: false }) })
  },

  inputNote(e) { this.setData({ note: e.detail.value }) },

  saveNote() {
    wx.setStorageSync('plan_' + this.data.detail.appointment_id, this.data.note)
    wx.showToast({ title: '方案已保存', icon: 'success' })
  },

  advance(e) {
    const id = e.currentTarget.dataset.id
    const ev = e.currentTarget.dataset.event
    req('/api/appointments/' + id + '/event', 'POST', { event: ev })
      .then(() => { wx.showToast({ title: '已更新', icon: 'success' }); this.loadDetail() })
      .catch((err) => wx.showModal({ title: '操作失败', content: err.message || '请重试', showCancel: false }))
  }
})
