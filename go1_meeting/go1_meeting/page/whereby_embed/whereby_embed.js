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
		const script = document.createElement('script');
        script.src = "https://cdn.srv.whereby.com/embed/v2-embed.js";
        script.type = "module";
        document.head.appendChild(script);
		$(`
        <div class="container">
            <whereby-embed room="https://jaffar008.whereby.com/77a67836-40f4-4442-a159-6f745dcc7fb8?roomKey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZWV0aW5nSWQiOiI5MDgwMzU4NSIsInJvb21SZWZlcmVuY2UiOnsicm9vbU5hbWUiOiIvNzdhNjc4MzYtNDBmNC00NDQyLWExNTktNmY3NDVkY2M3ZmI4Iiwib3JnYW5pemF0aW9uSWQiOiIyNzAxOTMifSwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5zcnYud2hlcmVieS5jb20iLCJpYXQiOjE3MjY2NTY0NDUsInJvb21LZXlUeXBlIjoibWVldGluZ0hvc3QifQ.iHFYl3BNpiyoTHl20zHJhXdD5r93GLxwUAZjipZ-wn0" />
        </div>
    </body>
			`).appendTo(this.page.main);
	}
}