frappe.pages['whereby-embed'].on_page_load = function(wrapper) {
	frappe.wherebyembed = new WhereByEmbed(wrapper);


}

class WhereByEmbed{
	constructor(parent) {
		frappe.ui.make_app_page({
			parent: parent,
			title: __("whereby-embed"),
			single_column: false,
			card_layout: false,
		});
		

		this.parent = parent;
		this.page = this.parent.page;
		this.make();
	}
	make(){
		const searchParam = new URLSearchParams(window.location.search)
        console.log(searchParam.has("meeting_id"))
        if (searchParam.has("meeting_id")) {
            console.log("working...")
			console.log(searchParam.get("meeting_id"))
        }
		const script = document.createElement('script');
        script.src = "https://cdn.srv.whereby.com/embed/v2-embed.js";
        script.type = "module";
        document.head.appendChild(script);
		$(`
        <div class="container">
            <whereby-embed room="${searchParam.get("meeting_id")}" />
        </div>
    </body>
			`).appendTo(this.page.main);
	}
}