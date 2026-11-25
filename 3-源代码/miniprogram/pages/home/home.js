const MENU = {
  PATIENT: [
    { name: '预约就诊', icon: '📅', url: '/packagePatient/book/book' },
    { name: '我的预约', icon: '📋', url: '/packagePatient/mine/mine' }
  ],
  RECEPTION: [
    { name: '当日名单', icon: '📞', url: '/packageReception/today/today' }
  ],
  DOCTOR: [
    { name: '病历摘要', icon: '🩺', url: '/packageDoctor/summary/summary' },
    { name: '治疗方案', icon: '📝', url: '/packageDoctor/plan/plan' }
  ],
  NURSE: [
    { name: '分诊指引', icon: '🧤', url: '/packageNurse/triage/triage' }
  ],
  DIRECTOR: [
    { name: '经营指标', icon: '📊', url: '/packageDirector/metrics/metrics' }
  ]
}

const ROLE_NAME = {
  PATIENT: '患者', RECEPTION: '前台', DOCTOR: '医生',
  NURSE: '护士', DIRECTOR: '院长'
}

Page({
  data: { role: '', roleName: '', menu: [] },

  onShow() {
    const role = wx.getStorageSync('role')
    if (!role) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.setData({
      role,
      roleName: ROLE_NAME[role] || role,
      menu: MENU[role] || []
    })
  },

  open(e) {
    wx.navigateTo({ url: e.currentTarget.dataset.url })
  },

  goReminders() {
    wx.navigateTo({ url: '/pages/reminders/reminders' })
  },

  logout() {
    wx.removeStorageSync('role')
    wx.removeStorageSync('token')
    wx.reLaunch({ url: '/pages/login/login' })
  }
})