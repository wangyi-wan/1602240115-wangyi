const { req } = require('../../utils/request.js')

Page({
  data: {
    picked: '',
    roles: [
      { key: 'PATIENT',   name: '患者', desc: '预约 / 改约 / 查看记录' },
      { key: 'RECEPTION', name: '前台', desc: '到诊登记 / 代客建档' },
      { key: 'DOCTOR',    name: '医生', desc: '病历摘要 / 治疗方案' },
      { key: 'NURSE',     name: '护士', desc: '分诊指引 / 器械准备' },
      { key: 'DIRECTOR',  name: '院长', desc: '经营指标 / 失约明细' }
    ]
  },

  pick(e) {
    this.setData({ picked: e.currentTarget.dataset.key })
  },

  login() {
    if (!this.data.picked) {
      wx.showToast({ title: '请先选身份', icon: 'none' })
      return
    }
    wx.setStorageSync('role', this.data.picked)

    // 拿真实 openid：wx.login 拿 code → 后端换 openid
    // （只有填了正式小程序凭据才成功；测试号会自动降级，不影响登录）
    wx.login({
      success: (res) => {
        if (res.code) {
          req('/api/auth/login', 'POST', { code: res.code })
            .then((data) => {
              wx.setStorageSync('openid', data.openid)
              wx.setStorageSync('token', data.token || ('demo-token-' + this.data.picked))
            })
            .catch(() => {
              wx.setStorageSync('token', 'demo-token-' + this.data.picked)
            })
            .finally(() => { wx.reLaunch({ url: '/pages/home/home' }) })
        } else {
          wx.setStorageSync('token', 'demo-token-' + this.data.picked)
          wx.reLaunch({ url: '/pages/home/home' })
        }
      },
      fail: () => {
        wx.setStorageSync('token', 'demo-token-' + this.data.picked)
        wx.reLaunch({ url: '/pages/home/home' })
      }
    })
  }
})