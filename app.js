document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('card-container');
  const lastUpdateElem = document.getElementById('last-update');

  try {
    // キャッシュ回避用のタイムスタンプ付きで取得
    const res = await fetch(`./data/feed.json?t=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTPエラー: ${res.status}`);
    const data = await res.json();

    if (!data || data.length === 0) {
      container.innerHTML = 'データが空です。';
      return;
    }

    // 投稿日時（pub_date）が新しい順にソート（投稿がない選手は後ろへ）
    data.sort((a, b) => {
      const timeA = a.latest_post && a.latest_post.pub_date ? new Date(a.latest_post.pub_date).getTime() : 0;
      const timeB = b.latest_post && b.latest_post.pub_date ? new Date(b.latest_post.pub_date).getTime() : 0;
      return timeB - timeA; // 降順（新しいものが上）
    });

    lastUpdateElem.textContent = `最終同期: ${new Date().toLocaleTimeString('ja-JP')} (最新投稿順)`;
    container.innerHTML = '';

    data.forEach(item => {
      const card = document.createElement('div');
      card.className = 'card';

      let postHtml = '直近の投稿データがありません';
      if (item.latest_post) {
        const timeStr = item.latest_post.pub_date ? new Date(item.latest_post.pub_date).toLocaleString('ja-JP') : '日時不明';
        const imgHtml = item.latest_post.media_url ? `` : '';
        postHtml = `
          
            
              ⏱ ${timeStr}
              via ${item.platform}
            
            ${item.latest_post.text || '（画像または動画のみの投稿）'}
            ${imgHtml}
          
        `;
      }

      let btnGroup = '';
      if (item.x_username) btnGroup += `Xを見る`;
      if (item.instagram_username) btnGroup += `Instaを見る`;
      if (item.ibuki_url) btnGroup += `IBUKI GPS`;
      btnGroup += '';

      const avatar = item.avatar_url || 'https://via.placeholder.com/100?text=No+Img';
      const ageText = item.age ? ` (${item.age}歳)` : '';

      card.innerHTML = `
        
          
          
            No.${item.bib} ${item.name}${ageText}
            ${item.info || ''}
          
        
        ${postHtml}
        ${btnGroup}
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `読み込みエラー: ${err.message}data/feed.json が正しく出力されているか確認してください。`;
  }
});
