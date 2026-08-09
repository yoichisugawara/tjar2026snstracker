document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('card-container');
  const lastUpdateElem = document.getElementById('last-update');

  try {
    const res = await fetch(`./data/feed.json?t=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTPエラー: ${res.status}`);
    const data = await res.json();

    if (!data || data.length === 0) {
      container.innerHTML = 'データが空です。';
      return;
    }

    // 最新投稿順にソート（投稿がない選手は下へ）
    data.sort((a, b) => {
      const timeA = a.latest_post && a.latest_post.pub_date ? new Date(a.latest_post.pub_date).getTime() : 0;
      const timeB = b.latest_post && b.latest_post.pub_date ? new Date(b.latest_post.pub_date).getTime() : 0;
      return timeB - timeA;
    });

    if (lastUpdateElem) {
      lastUpdateElem.textContent = `最終同期: ${new Date().toLocaleTimeString('ja-JP')} (最新投稿順)`;
    }

    container.innerHTML = '';

    data.forEach(item => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.cssText = 'background:#fff; border-radius:12px; padding:16px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,0.08);';

      // 投稿部分
      let postHtml = '直近の投稿データがありません';
      
      if (item.latest_post) {
        const timeStr = item.latest_post.pub_date ? new Date(item.latest_post.pub_date).toLocaleString('ja-JP') : '日時不明';
        const imgHtml = item.latest_post.media_url ? `` : '';
        
        postHtml = `
          
            
              ⏱ ${timeStr}
              via ${item.platform || 'SNS'}
            
            ${item.latest_post.text || '（画像または動画のみの投稿）'}
            ${imgHtml}
          
        `;
      }

      // ボタン群
      let btnHtml = '';
      if (item.x_username) {
        btnHtml += `X(Twitter)`;
      }
      if (item.instagram_username) {
        btnHtml += `Instagram`;
      }
      if (item.ibuki_url) {
        btnHtml += `IBUKI GPS`;
      }
      btnHtml += '';

      const avatar = item.avatar_url || 'https://via.placeholder.com/100?text=No+Img';
      const ageText = item.age ? ` (${item.age}歳)` : '';

      card.innerHTML = `
        
          
          
            No.${item.bib} ${item.name}${ageText}
            ${item.info || ''}
          
        
        ${postHtml}
        ${btnHtml}
      `;

      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `読み込みエラー: ${err.message}`;
  }
});
