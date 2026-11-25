// pages/reminders/reminders.js —— 提醒发送记录（第 9 章）
// 这一页是"消息网关可替换"的可视化证据：
// 走的是桩通道还是真微信、有没有触发降级，一眼看得见。
const { req } = require('../../utils/request.js')

const CHANNEL_NAME = {
  WECHAT: '微信订阅消息',
  SMS: '短信',
  MANUAL: '人工外呼',
  STUB: '桩通道'
}

const RESULT_NAME = {
  OK: '已送达',
  STUB: '桩送达',
  FAIL: '失败',
  MANUAL: '转人工'
}

Page({
  data: {
    items: [],
    channel: '',
    channelName: '',
    templateConfigured: false,
    loading: false
  },

  onShow() {
    this.load()
  },

  load() {
    this.setData({ loading: true })
    req('/api/reminders/outbox?limit=30')
      .then((res) => {
        const items = (res.items || []).map((it) => ({
          ...it,
          channelName: CHANNEL_NAME[it.channel] || it.channel,
          resultName: RESULT_NAME[it.result] || it.result
        }))
        this.setData({
          items,
          channel: res.channel || '',
          channelName: CHANNEL_NAME[res.channel] || res.channel || '未知',
          templateConfigured: res.template_configured,
          loading: false
        })
      })
      .catch((err) => {
        this.setData({ loading: false })
        wx.showToast({ title: err.message || '加载失败', icon: 'none' })
      })
  },

  // 演示降级链：假装主通道挂了，看它怎么一路降到人工外呼
  demoFallback() {
    wx.showLoading({ title: '发送中' })
    req('/api/reminders/dispatch?force_fail=true', 'POST', {})
      .then((res) => {
        wx.hideLoading()
        const n = (res.results || []).length
        wx.showModal({
          title: '降级链演示完成',
          content: n ? `已处理 ${n} 条，链路见下方记录` : '当前没有到期的提醒计划',
          showCancel: false
        })
        this.load()
      })
      .catch((err) => {
        wx.hideLoading()
        wx.showToast({ title: err.message || '失败', icon: 'none' })
      })
  }
})
