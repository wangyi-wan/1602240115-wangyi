const { request, BASE_URL } = require('../../utils/request')

Page({
  data: {
    patients: [{ id: 1, name: '张三' }, { id: 2, name: '李四' }],
    chairs: [{ id: 1, code: 'A1' }, { id: 2, code: 'A2' }],
    slots: ['09:00', '09:30', '10:00', '10:30', '11:00', '14:00', '14:30', '15:00'],
    patientName: '',
    chairCode: '',
    date: '2026-11-02',
    slot: '',
    loading: false,
    baseUrl: BASE_URL
  },

  onPatient(e) {
    const p = this.data.patients[Number(e.detail.value)]
    this.setData({ patientName: p.name, patientId: p.id })
  },

  onChair(e) {
    const c = this.data.chairs[Number(e.detail.value)]
    this.setData({ chairCode: c.code, chairId: c.id })
  },

  onDate(e) {
    this.setData({ date: e.detail.value })
  },

  onSlot(e) {
    this.setData({ slot: this.data.slots[Number(e.detail.value)] })
  },

  async submit() {
    const { patientId, chairId, date, slot } = this.data
    if (!patientId || !chairId || !slot) {
      wx.showToast({ title: '请把四项都选完', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    try {
      const res = await request('/api/appointments', 'POST', {
        patient_id: patientId,
        chair_id: chairId,
        start_time: `${date}T${slot}:00`,
        minutes: 30
      })
      wx.showModal({
        title: '预约成功',
        content: `单号 ${res.appointment_id}，状态 ${res.status}`,
        showCancel: false
      })
    } catch (err) {
      // 失败提示已经在 request.js 里弹过了，这里不用重复
      console.error(err)
    } finally {
      this.setData({ loading: false })
    }
  }
})