Created At: 2026-10-02T15:23:08+05:30
Completed At: 2026-10-02T15:23:08+05:30
File Path: `file:///c:/Users/vedan/OneDrive/Documents/betting%20app/index.html`
Total Lines: 2817
Total Bytes: 158346
Showing lines 2700 to 2817
The following code has been modified to include a line number before every line, in the format: <line_number>: <original_line>. Please note that any changes targeting the original code should remove the line number, colon, and leading space.
2700: 
2701:         function openLoginModal() {
2702:             document.getElementById('authModal').classList.remove('hidden');
2703:         }
2704: 
2705:         function closeAuthModal() {
2706:             document.getElementById('authModal').classList.add('hidden');
2707:         }
2708: 
2709:         function switchAuthTab(mode) {
2710:             authMode = mode;
2711:             const tabLogin = document.getElementById('authTabLogin');
2712:             const tabReg = document.getElementById('authTabRegister');
2713:             const submitBtn = document.getElementById('btnSubmitAuth');
2714: 
2715:             if (mode === 'login') {
2716:                 tabLogin.className = "py-2 rounded-lg bg-amber-500 text-purple-950";
2717:                 tabReg.className = "py-2 rounded-lg text-slate-400 hover:text-white";
2718:                 submitBtn.innerText = "Log In";
2719:             } else {
2720:                 tabReg.className = "py-2 rounded-lg bg-amber-500 text-purple-950";
2721:                 tabLogin.className = "py-2 rounded-lg text-slate-400 hover:text-white";
2722:                 submitBtn.innerText = "Create Account";
2723:             }
2724:         }
2725: 
2726:         function quickFillAuth(uname, pass) {
2727:             document.getElementById('authUsernameInput').value = uname;
2728:             document.getElementById('authPasswordInput').value = pass;
2729:             switchAuthTab('login');
2730:             submitAuthForm();
2731:         }
2732: 
2733:         async function submitAuthForm() {
2734:             const uname = document.getElementById('authUsernameInput').value.trim();
2735:             const pass = document.getElementById('authPasswordInput').value.trim();
2736: 
2737:             if (!uname || !pass) {
2738:                 showGeneralModal("Missing Fields", "Please enter both username and password.", "⚠️");
2739:                 return;
2740:             }
2741: 
2742:             const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
2743:             const res = await apiRequest(endpoint, 'POST', { username: uname, password: pass });
2744: 
2745:             if (res && res.status === 'success') {
2746:                 authToken = res.token;
2747:                 updateCurrentUserUI(res.user);
2748:                 playSound('win');
2749:                 closeAuthModal();
2750:                 showGeneralModal("Authentication Success", res.message, "🎉");
2751:             } else if (res && res.message) {
2752:                 showGeneralModal("Authentication Failed", res.message, "❌");
2753:             } else {
2754:                 const role = uname === 'admin' ? 'admin' : 'user';
2755:                 authToken = "demo-local-token";
2756:                 updateCurrentUserUI({
2757:                     username: uname,
2758:                     role: role,
2759:                     balance: localWallet
2760:                 });
2761:                 closeAuthModal();
2762:                 showGeneralModal("Logged In", `Logged in as ${uname} (${role.toUpperCase()}) in offline mode.`, "✅");
2763:             }
2764:         }
2765: 
2766:         // ==============================================
2767:         // MODALS
2768:         // ==============================================
2769:         function openRulesModal() {
2770:             document.getElementById('rulesModal').classList.remove('hidden');
2771:         }
2772:         function closeRulesModal() {
2773:             document.getElementById('rulesModal').classList.add('hidden');
2774:         }
2775: 
2776:         function showGeneralModal(heading, msg, icon = "🎉") {
2777:             document.getElementById('modalHeading').innerText = heading;
2778:             document.getElementById('modalMessage').innerHTML = msg;
2779:             document.getElementById('modalIcon').innerText = icon;
2780:             document.getElementById('generalModal').classList.remove('hidden');
2781:         }
2782:         function closeGeneralModal() {
2783:             document.getElementById('generalModal').classList.add('hidden');
2784:         }
2785: 
2786:         // ==============================================
2787:         // INITIALIZATION
2788:         // ==============================================
2789:         window.onload = async function() {
2790:             drawFunRouletteWheel(0, 0, 1.0);
2791:             startAmbientWheelLoop();
2792:             drawAviatorStatic();
2793:             initMinesGrid();
2794: 
2795:             const userRes = await apiRequest('/api/auth/me');
2796:             if (userRes && userRes.status === 'success') {
2797:                 updateCurrentUserUI(userRes.user);
2798:             } else {
2799:                 updateCurrentUserUI(currentUser);
2800:             }
2801: 
2802:             // Initial recent history
2803:             const histRes = await apiRequest('/api/fun_roulette/history');
2804:             if (histRes && histRes.history) {
2805:                 updateRouletteHistoryUI(histRes.history);
2806:             }
2807: 
2808:             // Populate initial color beads
2809:             [
2810:                 { n: 7, c: 'GREEN' }, { n: 2, c: 'RED' }, { n: 0, c: 'VIOLET' },
2811:                 { n: 8, c: 'RED' }, { n: 3, c: 'GREEN' }
2812:             ].forEach(b => addColorHistoryBead(b.n, b.c));
2813:         };
2814:     </script>
2815: </body>
2816: 
2817: </html>
The above content does NOT show the entire file contents. If you need to view any lines of the file which were not shown to complete your task, call this tool again to view those lines.
