function selecttext(){
  this.select();
}
function copyEmail() {
  var copyText = document.getElementById("copyThis");
  copyText.select();
  document.execCommand("Copy");
}
