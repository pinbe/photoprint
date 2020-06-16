export class WidgetBasedFormManager {
    private editArea: HTMLDivElement;
    constructor(editingAreaSelector: string) {
        this.editArea = document.querySelector(editingAreaSelector);
        console.log(this.editArea);
    }
}