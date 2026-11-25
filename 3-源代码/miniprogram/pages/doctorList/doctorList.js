Page({
  data: {
    doctorList: [
      {id:1, name:"张医生", department:"正畸科"},
      {id:2, name:"李医生", department:"牙体牙髓科"},
      {id:3, name:"王医生", department:"口腔外科"}
    ]
  },
  onLoad() {

  },
  goAppointment(e){
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/appointment/appointment?doctorId=${id}`
    })
  }
})
