// One-click role logins on /login. The server only returns accounts when
// the site runs in demo mode (hms_demo_mode), so customer installs show nothing.
frappe.ready(() => {
	if (window.location.pathname !== "/login") return;

	frappe.call("hospital_saas.demo_mode.get_demo_logins").then((r) => {
		const logins = r.message || [];
		const card = document.querySelector("section.for-login .login-content");
		if (!logins.length || !card) return;

		const panel = document.createElement("div");
		panel.className = "hms-demo-logins";
		panel.innerHTML = `
			<div class="hms-demo-title">${__("Demo logins")}</div>
			<div class="hms-demo-hint">${__("Pick a role to sign in. Password for all")}: <code></code></div>
			<div class="hms-demo-grid"></div>`;
		panel.querySelector("code").textContent = logins[0].password;

		const grid = panel.querySelector(".hms-demo-grid");
		logins.forEach((login) => {
			const button = document.createElement("button");
			button.type = "button";
			button.className = "hms-demo-role";
			button.title = login.email;
			button.innerHTML = "<strong></strong><span></span>";
			button.querySelector("strong").textContent = login.role;
			button.querySelector("span").textContent = login.name;
			button.addEventListener("click", () => {
				document.querySelector("section.for-login #login_email").value = login.email;
				document.querySelector("section.for-login #login_password").value = login.password;
				$("section.for-login .form-login").trigger("submit");
			});
			grid.appendChild(button);
		});
		card.appendChild(panel);
	});
});

frappe.ready(() => {
	if (window.location.pathname !== "/login") return;
	const style = document.createElement("style");
	style.textContent = `
		.hms-demo-logins { border-top: 1px solid var(--border-color, #e2e8f0); padding-top: 16px; }
		.hms-demo-title { font-weight: 600; font-size: 14px; }
		.hms-demo-hint { font-size: 12px; color: var(--text-muted, #64748b); margin: 2px 0 10px; }
		.hms-demo-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
		.hms-demo-role { display: flex; flex-direction: column; align-items: flex-start; text-align: left;
			padding: 8px 10px; border: 1px solid var(--border-color, #e2e8f0); border-radius: 8px;
			background: var(--fg-color, #fff); cursor: pointer; }
		.hms-demo-role:hover { border-color: #0e7c6b; background: #f0faf8; }
		.hms-demo-role strong { font-size: 13px; color: #0e7c6b; }
		.hms-demo-role span { font-size: 12px; color: var(--text-muted, #64748b); }`;
	document.head.appendChild(style);
});
