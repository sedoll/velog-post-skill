// Run with javascript_tool while velog's publish panel (출간하기 / 수정하기) is open.
// velog creates a temporary <input type=file> and calls .click() on it when "썸네일 업로드" is pressed,
// which would open the native file picker (Claude can't use it). This catches that input, attaches it
// to the page (hidden) without opening the picker, so `file_upload` can target it.
(() => {
  const orig = HTMLInputElement.prototype.click;
  HTMLInputElement.prototype.click = function () {
    if (this.type === 'file') {
      this.id = 'claude-thumb-input';
      this.style.display = 'none';
      document.body.appendChild(this);
      HTMLInputElement.prototype.click = orig;
      return;
    }
    return orig.call(this);
  };
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => ['썸네일 업로드', '재업로드'].includes(b.textContent.trim()));
  if (!btn) { HTMLInputElement.prototype.click = orig; return 'thumbnail button not found (is the publish panel open?)'; }
  btn.click();
  const inp = document.getElementById('claude-thumb-input');
  return inp ? 'file input captured (accept=' + inp.accept + ')' : 'file input not captured';
})()
