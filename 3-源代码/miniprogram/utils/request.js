// 请求封装：自动选择后端地址，避免 IP 来回改的痛苦。
//
// 规则：
//   1) 在「微信开发者工具」里预览时 → 连本机 127.0.0.1（这个地址永远不变）
//   2) 在「真机预览 / 体验版」里     → 连云服务器公网 IP（下面 LAN_IP）
//
// 注意：LAN_IP 现在是腾讯云轻量服务器的公网 IP，固定不变。
// 换服务器 / 重装系统后 IP 会变，把下面 LAN_IP 改成新的公网 IP 即可。
const LAN_IP = '49.232.168.130'

function getBaseUrl() {
  try {
    // platform 为 'devtools' 表示运行在开发者工具里
    if (wx.getSystemInfoSync().platform === 'devtools') {
      return 'http://127.0.0.1:8000'
    }
  } catch (e) { /* 拿不到信息就走下面的默认值 */ }
  return 'http://' + LAN_IP + ':8000'
}

const BASE_URL = getBaseUrl()

// 页面里统一用 req(path, method, data)
function req(path, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method,
      data,
      header: {
        'content-type': 'application/json',
        'Authorization': wx.getStorageSync('token') || ''
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          // 把后端的 detail 抛出来，页面里能直接显示给人看
          const msg = (res.data && res.data.detail) || ('请求失败 ' + res.statusCode)
          wx.showToast({ title: msg, icon: 'none', duration: 2500 })
          reject(new Error(msg))
        }
      },
      fail(err) {
        wx.showToast({ title: '连不上服务器', icon: 'none' })
        reject(err)
      }
    })
  })
}

// 导出 req（页面主要用它）；同时兼容老写法 request / BASE_URL
module.exports = { req, request: req, BASE_URL }
