const { req } = require('../../utils/request.js')
const { STATUS_LABEL, todayStr } = require('../../utils/util.js')

Page({
  data: { total: 0, todayCount: 0, done: 0, active: 0, cancelled: 0, breakdown: [], loading: true },

  onShow() { this.load() },

  load() {
    this.setData({ loading: true })
    const date = todayStr()
    Promise.all([
      req('/api/appointments'),
      req('/api/appointments?date=' + date)
    ]).then(([all, today]) => {
      const a = all || []
      const t = today || []
      const count = {}
      a.forEach((x) => { count[x.status] = (count[x.status] || 0) + 1 })
      const breakdown = Object.keys(STATUS_LABEL)
        .filter((s) => count[s])
        .map((s) => ({ label: STATUS_LABEL[s], num: count[s] }))
      this.setData({
        total: a.length,
        todayCount: t.length,
        done: count['DONE'] || 0,
        active: (count['BOOKED'] || 0) + (count['CONFIRMED'] || 0) + (count['ARRIVED'] || 0) + (count['IN_PROGRESS'] || 0),
        cancelled: (count['CANCELLED'] || 0) + (count['NO_SHOW'] || 0),
        breakdown,
        loading: false
      })
    }).catch(() => {
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    })
  }
})
