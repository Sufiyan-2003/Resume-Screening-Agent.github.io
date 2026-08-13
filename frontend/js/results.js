let run;const runId=sessionStorage.getItem('runId')||new URLSearchParams(location.search).get('run');const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
async function init(){if(!runId){location.href='/';return}const res=await fetch(`/api/results/${runId}`);if(!res.ok){alert('Results were not found.');location.href='/';return}run=await res.json();document.querySelector('#job-title').textContent=run.job_title;csv.href=`/api/export/${runId}/csv`;json.href=`/api/export/${runId}/json`;const avg=run.candidates.reduce((a,c)=>a+c.score,0)/run.candidates.length, strong=run.candidates.filter(c=>c.recommendation==='Strong Match').length, short=run.candidates.filter(c=>c.score>=65).length;summary.innerHTML=[[run.total_candidates,'Total candidates'],[avg.toFixed(1)+'%','Average score'],[strong,'Strong matches'],[short,'Shortlisted (65%+)']].map(x=>`<div class="card"><strong>${x[0]}</strong><span>${x[1]}</span></div>`).join('');render()}
function render(){const q=search.value.toLowerCase(), filterVal=filter.value, field=sort.value;const candidates=[...run.candidates].filter(c=>c.name.toLowerCase().includes(q)&&(!filterVal||c.recommendation===filterVal)).sort((a,b)=>b[field]-a[field]);rows.innerHTML=candidates.map(c=>`<tr><td>#${c.rank}</td><td>${esc(c.name)}<br><small>${esc(c.email||'')}</small></td><td><b>${c.score.toFixed(1)}%</b></td><td>${c.skills_score.toFixed(0)}%</td><td>${c.experience_score.toFixed(0)}%</td><td>${c.education_score.toFixed(0)}%</td><td><span class="pill ${c.recommendation.split(' ')[0]}">${c.recommendation}</span></td><td><button onclick="showDetail(${c.id})">View details</button></td></tr>`).join('')||'<tr><td colspan="8">No candidates match these filters.</td></tr>'}
function badges(items, missing=false){return `<div class="badges ${missing?'missing':''}">${items.length?items.map(x=>`<span>${esc(x)}</span>`).join(''):'<span>None found</span>'}</div>`}
async function showDetail(id) {
    try {
        console.log("Opening candidate details:", id);

        const response = await fetch(`/api/candidate/${id}`);

        console.log("Candidate API status:", response.status);

        if (!response.ok) {
            throw new Error(`Failed to load candidate. HTTP ${response.status}`);
        }

        const c = await response.json();

        console.log("Candidate data:", c);

        const detailDialog = document.getElementById("detail");
        const detailContent = document.getElementById("detailContent");

        if (!detailDialog) {
            throw new Error(
                'Could not find <dialog id="detail"> in results.html'
            );
        }

        if (!detailContent) {
            throw new Error(
                'Could not find element with id="detailContent" in results.html'
            );
        }

        detailContent.innerHTML = `
            <h2>${esc(c.name)}</h2>

            <p>
                ${esc(c.email || "Email not found")}
                ·
                ${esc(c.phone || "Phone not found")}
            </p>

            <h3>
                ${Number(c.score).toFixed(1)}%
                ·
                ${esc(c.recommendation)}
            </h3>

            <h3>Score Breakdown</h3>

            ${[
                ["Semantic Match", c.semantic_score],
                ["Skills Match", c.skills_score],
                ["Experience Match", c.experience_score],
                ["Education Match", c.education_score],
                ["Preferred Skills", c.preferred_skills_score]
            ].map(([label, value]) => `
                <div class="score-row">
                    <b>${label}: ${Number(value || 0).toFixed(0)}%</b>
                    <div class="bar">
                        <i style="width:${Math.min(100, Math.max(0, Number(value || 0)))}%"></i>
                    </div>
                </div>
            `).join("")}

            <h3>Matched Skills</h3>
            ${badges(c.matched_skills || [])}

            <h3>Missing Required Skills</h3>
            ${badges(c.missing_skills || [], true)}

            <h3>Additional Skills</h3>
            ${badges(c.additional_skills || [])}

            <h3>Reasoning</h3>
            <p>${esc(c.reasoning || "No reasoning available.")}</p>
        `;

        detailDialog.showModal();

    } catch (error) {
        console.error("View Details error:", error);
        alert(`Unable to load candidate details:\n\n${error.message}`);
    }
}
search.oninput=render;filter.onchange=render;sort.onchange=render;init();
