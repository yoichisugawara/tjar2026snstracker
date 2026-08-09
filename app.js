document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('card-container');
  const lastUpdateElem = document.getElementById('last-update');

  try {
    const res = await fetch(`data/feed.json?t=${Date.now()}`);
    if (!res.ok) throw new Error('データが見つかりません');
    const data = await res.json();

    lastUpdateElem.textContent = `最終同期: ${new Date().toLocaleTimeString('ja-JP')} (最新順表示)`;
    container.innerHTML = '';

    data.forEach(item => {
      const card = document.createElement('div');
      card.className = 'card';

      let postHtml = '<div class="post-box"><p class="post-text">直近の投稿データがありません</p></div>';
      if (item.latest_post) {
        const timeStr = item.latest_post.pub_date ? new Date(item.latest_post.pub_date).toLocaleString('ja-JP') : '日時不明';
        const imgHtml = item.latest_post.media_url ? `<img src="${item.latest_post.media_url}" class="post-media" loading="lazy">` : '';
        postHtml = `
          <div class="post-box">
            <div class="post-header">
              <span>⏱ ${timeStr}</span>
              <span>via ${item.platform}</span>
            </div>
            <p class="post-text">${item.latest_post.text || '（画像または動画のみの投稿）'}</p>
            ${imgHtml}
          </div>
        `;
      }

      let btnGroup = '<div class="btn-group">';
      if (item.x_username) btnGroup += `<a href="https://x.com/${item.x_username}" target="_blank" class="btn">Xを見る</a>`;
      if (item.instagram_username) btnGroup += `<a href="https://instagram.com/${item.instagram_username}" target="_blank" class="btn">Instaを見る</a>`;
      if (item.ibuki_url) btnGroup += `<a href="${item.ibuki_url}" target="_blank" class="btn ibuki">IBUKI GPS</a>`;
      btnGroup += '</div>';

      const avatar = item.avatar_url || 'https://via.placeholder.com/100?text=No+Img';
      const ageText = item.age ? ` (${item.age}歳)` : '';

      card.innerHTML = `
        <div class="profile-header">
          <img src="${avatar}" class="avatar" alt="${item.name}">
          <div class="meta">
            <div class="bib-name">No.${item.bib} ${item.name}${ageText}</div>
            <div class="sub-info">${item.info || ''}</div>
          </div>
        </div>
        ${postHtml}
        ${btnGroup}
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<p style="color:red; text-align:center;">エラー: ${err.message}</p>`;
  }
});
