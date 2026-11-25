// pages/appointment/appointment.js
const { req } = require('../../utils/request.js')

// 时段描述 → 具体开始时刻（与 timeList 一一对齐）
const START_TIMES = ['08:30:00', '10:00:00', '14:00:00', '15:30:00']

function todayStr() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

Page({
  data: {
    doctorId: '',
    doctorName: '',
    selectDate: '',
    timeIndex: 0,
    timeList: ['上午 8:30-10:00', '上午10:00-11:30', '下午14:00-15:30', '下午15:30-17:00'],
    phone: '',

    // 从后端拉取的下拉数据
    patientNames: [],
    patientIds: [],
    patientIndex: 0,
    chairNames: [],
    chairIds: [],
    chairIndex: 0,

    today: todayStr(),
    submitting: false
  },

  onLoad(options) {
    const id = options.doctorId
    this.setData({ doctorId: id })

    if (id == 1) {
      this.setData({ doctorName: '张医生（正畸科）' })
    } else if (id == 2) {
      this.setData({ doctorName: '李医生（牙体牙髓科）' })
    } else if (id == 3) {
      this.setData({ doctorName: '王医生（口腔外科）' })
    }

    this.loadPatients()
    this.loadChairs()
  },

  // 拉取就诊人（对应 t_person + t_patient）
  loadPatients() {
    req('/api/patients').then((list) => {
      if (!list || list.length === 0) return
      this.setData({
        patientNames: list.map((p) => p.name),
        patientIds: list.map((p) => p.patient_id),
        patientIndex: 0
      })
    }).catch((err) => {
      wx.showToast({ title: '就诊人加载失败', icon: 'none' })
      console.error(err)
    })
  },

  // 拉取牙椅（对应 t_dental_chair）
  loadChairs() {
    req('/api/chairs').then((list) => {
      if (!list || list.length === 0) return
      this.setData({
        chairNames: list.map((c) => c.code),
        chairIds: list.map((c) => c.chair_id),
        chairIndex: 0
      })
    }).catch((err) => {
      wx.showToast({ title: '牙椅加载失败', icon: 'none' })
      console.error(err)
    })
  },

  changeDate(e) {
    this.setData({ selectDate: e.detail.value })
  },

  changeTime(e) {
    this.setData({ timeIndex: e.detail.value })
  },

  changePatient(e) {
    this.setData({ patientIndex: e.detail.value })
  },

  changeChair(e) {
    this.setData({ chairIndex: e.detail.value })
  },

  inputPhone(e) {
    this.setData({ phone: e.detail.value })
  },

  // 预约成功后：先要一次订阅授权，再让后端建提醒计划
  // 测试号没有 AppSecret、配不了模板，所以这一段会自动跳过，不影响主流程
  askRemind(appointmentId) {
    // 正式小程序：把你在「订阅消息 → 我的模板」复制的模板 ID 填到引号里
    // 留空 = 走桩通道（不实发）。填了且后端三项凭据齐全，才会真弹授权框并实发
    const TMPL = ''

    const createPlan = (channel) => {
      req('/api/reminders/plan', 'POST', {
        appointment_id: appointmentId,
        openid: wx.getStorageSync('openid') || 'demo-openid'
      }).catch(() => {})   // 提醒失败不影响预约本身
    }

    if (!TMPL) {
      createPlan('STUB')
      return
    }
    wx.requestSubscribeMessage({
      tmplIds: [TMPL],
      success: (r) => {
        createPlan(r[TMPL] === 'accept' ? 'WECHAT' : 'STUB')
      },
      fail: () => createPlan('STUB')
    })
  },

  // 提交预约：真正调后端 POST /api/appointments
  submitOrder() {
    if (!this.data.selectDate) {
      wx.showToast({ title: '请选择预约日期', icon: 'none' })
      return
    }
    if (!/^1\d{10}$/.test(this.data.phone)) {
      wx.showToast({ title: '请填写11位手机号', icon: 'none' })
      return
    }
    if (this.data.patientIds.length === 0 || this.data.chairIds.length === 0) {
      wx.showToast({ title: '基础数据未加载完成', icon: 'none' })
      return
    }

    const start = `${this.data.selectDate}T${START_TIMES[this.data.timeIndex]}`
    const payload = {
      patient_id: this.data.patientIds[this.data.patientIndex],
      chair_id: this.data.chairIds[this.data.chairIndex],
      start_time: start,
      minutes: 30
    }

    this.setData({ submitting: true })
    req('/api/appointments', 'POST', payload)
      .then((res) => {
        this.askRemind(res.appointment_id)
        wx.showToast({ title: '预约成功', icon: 'success' })
        setTimeout(() => {
          wx.navigateBack()
        }, 800)
      })
      .catch((err) => {
        // 409 时段冲突、外键不存在等，都在这里提示
        wx.showModal({
          title: '预约失败',
          content: err.message || '请稍后重试',
          showCancel: false
        })
      })
      .finally(() => {
        this.setData({ submitting: false })
      })
  }
})
