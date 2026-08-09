document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('card-container');
  const lastUpdateElem = document.getElementById('last-update');

  try {
    const res = await fetch(`./data/feed.json?t=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTPエラー: ${res.status}`);
    const data = await res.json();

    if (!data || data.length === 0) {
      container.innerHTML = '<p style="text-align:center; padding:20px;">データが空です。</p>';
      return;
    }

    // 最新投稿順（投稿がない場合はゼッケン順）にソート
    data.sort((a, b) => {
      const timeA = a.latest_post && a.latest_post.pub_date ? new Date(a.latest_post.pub_date).getTime() : 0;
      const timeB = b.latest_post && b.latest_post.pub_date ? new Date(b.latest_post.pub_date).getTime() : 0;
      if (timeA === timeB) {
        return parseInt(a.bib) - parseInt(b.bib);
      }
      return timeB - timeA;
    });

    if (lastUpdateElem) {
      lastUpdateElem.textContent = `最終同期: ${new Date().toLocaleTimeString('ja-JP')}`;
    }

    container.innerHTML = '';

    data.forEach(item => {
      const card = document.createElement('div');
      card.style.cssText = 'background:#ffffff; border-radius:12px; padding:16px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,0.08); display:block;';

      // 1. プロフィールヘッダー部分
      const avatar = item.avatar_url || 'https://via.placeholder.com/100?text=No+Img';
      const ageText = item.age ? ` (${item.age}歳)` : '';
      
      const headerDiv = document.createElement('div');
      headerDiv.style.cssText = 'display:flex; align-items:center; gap:12px; margin-bottom:12px;';
      headerDiv.innerHTML = `
        <img src="${avatar}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; background:#e2e8f0; flex-shrink:0;">
        <div>
          <div style="font-weight:bold; font-size:1.05rem; color:#0f172a;">No.${item.bib} ${item.name}${ageText}</div>
          <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">${item.info || ''}</div>
        </div>
      `;
      card.appendChild(headerDiv);

      // 2. IBUKI 現在地ステータス表示（データがある場合）
      if (item.ibuki_status) {
        const ibukiDiv = document.createElement('div');
        ibukiDiv.style.cssText = 'background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; border-radius:8px; padding:8px 12px; margin-bottom:12px; font-size:0.85rem; font-weight:600; display:flex; align-items:center; gap:6px;';
        ibukiDiv.innerHTML = `<span>📍 IBUKI:</span> <span>${item.ibuki_status}</span>`;
        card.appendChild(ibukiDiv);
      }

      // 3. SNS投稿本文部分
      const postDiv = document.createElement('div');
      postDiv.style.cssText = 'background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; margin-bottom:12px;';

      if (item.latest_post) {
        let formattedDate = '日時不明';
        if (item.latest_post.pub_date) {
          const d = new Date(item.latest_post.pub_date);
          if (!isNaN(d.getTime())) {
            const month = d.getMonth() + 1;
            const date = d.getDate();
            const hours = String(d.getHours()).padStart(2, '0');
            const minutes = String(d.getMinutes()).padStart(2, '0');
            formattedDate = `${month}/${date} ${hours}:${minutes}`;
          }
        }

        const imgHtml = item.latest_post.media_url ? `<img src="${item.latest_post.media_url}" style="width:100%; max-height:300px; object-fit:cover; border-radius:6px; margin-top:8px; display:block;" loading="lazy">` : '';

        postDiv.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; color:#64748b; margin-bottom:6px;">
            <span style="font-weight:600; color:#0f172a;">⏱ ${formattedDate}</span>
            <span style="background:#e2e8f0; padding:2px 6px; border-radius:4px;">via ${item.platform || 'SNS'}</span>
          </div>
          <div style="font-size:0.9rem; line-height:1.5; color:#334155; white-space:pre-wrap; word-break:break-word;">${item.latest_post.text || '（画像または動画のみの投稿）'}</div>
          ${imgHtml}
        `;
      } else {
        // latest_post が null の場合の表示
        postDiv.innerHTML = `
          <div style="color:#64748b; font-size:0.85rem; text-align:center; padding:4px 0;">
            最新投稿データ未取得（Instagramで確認）
          </div>
        `;
      }
      card.appendChild(postDiv);

      // 4. ボタン部分
      const btnDiv = document.createElement('div');
      btnDiv.style.cssText = 'display:flex; gap:8px; flex-wrap:wrap;';

      if (item.x_username) {
        btnDiv.innerHTML += `<a href="https://x.com/${item.x_username}" target="_blank" rel="noopener" style="flex:1; min-width:120px; text-align:center; padding:10px 0; background:#000000; color:#ffffff; text-decoration:none; font-size:0.85rem; font-weight:bold; border-radius:6px; display:block;">Xを見る</a>`;
      }
      if (item.instagram_username) {
        // @ユーザー名 を含めたテキストで表示
        btnDiv.innerHTML += `<a href="https://instagram.com/${item.instagram_username}" target="_blank" rel="noopener" style="flex:1; min-width:120px; text-align:center; padding:10px 0; background:#e1306c; color:#ffffff; text-decoration:none; font-size:0.85rem; font-weight:bold; border-radius:6px; display:block;">Instaを見る (@${item.instagram_username})</a>`;
      }
      if (item.ibuki_url) {
        btnDiv.innerHTML += `<a href="${item.ibuki_url}" target="_blank" rel="noopener" style="flex:1; min-width:120px; text-align:center; padding:10px 0; background:#16a34a; color:#ffffff; text-decoration:none; font-size:0.85rem; font-weight:bold; border-radius:6px; display:block;">IBUKI GPS</a>`;
      }
      
      card.appendChild(btnDiv);
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<p style="color:#ef4444; text-align:center; padding:20px;">読み込みエラー: ${err.message}</p>`;
  }
});
