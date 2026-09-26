// One row per TagsGenerator category: a toggle and its share together.
//
// The node declares them as two widgets -- a BOOLEAN named after the
// category and a FLOAT named <category>_share -- because that is all
// INPUT_TYPES can express. Two stacked rows per category is ten rows for
// what reads as five settings, so here the pair is drawn as one: the
// toggle on the left, the share on the right, greyed out while the
// toggle is off.
//
// Both widgets stay in node.widgets. Only their appearance is merged:
// the boolean is hidden rather than removed, so widget order -- and with
// it serialisation and the prompt the backend receives -- is untouched.
import { app } from "../../scripts/app.js";

const NODE = "TagsGenerator";
const SHARE_SUFFIX = "_share";

// Read off the node rather than listed here: a category is any BOOLEAN
// that has a FLOAT named after it plus the suffix. A hardcoded list goes
// stale the moment CATEGORY_DEFAULTS gains an entry, and the symptom --
// one category rendering as two plain rows while the rest are merged --
// looks like a bug in the drawing code rather than a missing name.
function categoriesOf(node) {
    const names = new Set(node.widgets?.map(w => w.name) ?? []);
    return (node.widgets ?? [])
        .filter(w => w.type === "toggle" || typeof w.value === "boolean")
        .map(w => w.name)
        .filter(name => names.has(name + SHARE_SUFFIX));
}

export function isLowQuality() {
    return (app.canvas?.ds?.scale || 1) <= 0.5;
}

export function drawToggle(ctx, x, y, height, on) {
    const width = height * 1.5;
    const radius = height * 0.36;
    if (!isLowQuality()) {
        ctx.beginPath();
        ctx.roundRect(x + 4, y + 4, width - 8, height - 8, [height * 0.5]);
        ctx.globalAlpha = app.canvas.editor_alpha * 0.25;
        ctx.fillStyle = "rgba(255,255,255,0.45)";
        ctx.fill();
        ctx.globalAlpha = app.canvas.editor_alpha;
    }
    ctx.beginPath();
    const knobX = on ? x + width - radius - 5 : x + radius + 5;
    ctx.arc(knobX, y + height * 0.5, radius, 0, Math.PI * 2);
    ctx.fillStyle = on ? "#89B" : "#888";
    ctx.fill();
    return width;
}

// A share of -1 is "allowed, no cap" -- a number nobody wants to read as
// a percentage, so it gets a word instead.
function shareLabel(value) {
    if (value < 0) return "no cap";
    return `${Math.round(value * 100)}%`;
}

function makeRow(node, boolWidget, shareWidget) {
    const row = {
        type: "custom",
        name: shareWidget.name,
        options: shareWidget.options,
        // the row stands for both widgets, so it answers for both help
        // texts; without this the merged row would have none at all
        tooltip: `${boolWidget.options?.tooltip ?? ""}\n\n${
            shareWidget.options?.tooltip ?? ""}`.trim(),
        get value() { return shareWidget.value; },
        set value(v) { shareWidget.value = v; },
        // the real widgets serialise themselves; this one is decoration
        serializeValue() { return shareWidget.value; },
        computeSize(width) { return [width, LiteGraph.NODE_WIDGET_HEIGHT]; },
    };

    row.draw = function (ctx, node, width, y, height) {
        const margin = 15;
        const inner = margin * 0.33;
        const midY = y + height * 0.5;
        ctx.save();
        ctx.strokeStyle = LiteGraph.WIDGET_OUTLINE_COLOR;
        ctx.fillStyle = LiteGraph.WIDGET_BGCOLOR;
        ctx.beginPath();
        ctx.roundRect(margin, y, node.size[0] - margin * 2, height,
                      isLowQuality() ? [0] : [height * 0.5]);
        ctx.fill();
        if (!isLowQuality()) ctx.stroke();

        let x = margin + 6;
        this.toggleBounds = [x, drawToggle(ctx, x, y, height, boolWidget.value)];
        x += this.toggleBounds[1] + inner;

        if (isLowQuality()) { ctx.restore(); return; }
        if (!boolWidget.value) ctx.globalAlpha = app.canvas.editor_alpha * 0.4;

        ctx.fillStyle = LiteGraph.WIDGET_SECONDARY_TEXT_COLOR || "#999";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(boolWidget.name, x, midY);

        // arrows, so the share still reads and behaves like a number
        const right = node.size[0] - margin - 8;
        ctx.fillStyle = LiteGraph.WIDGET_TEXT_COLOR;
        ctx.textAlign = "right";
        ctx.fillText(shareLabel(shareWidget.value), right - 12, midY);
        ctx.textAlign = "center";
        ctx.fillText("◀", x + 4 + (right - x) * 0.62, midY);
        ctx.fillText("▶", right - 4, midY);
        this.decBounds = [x + (right - x) * 0.62 - 6, 16];
        this.incBounds = [right - 12, 16];
        ctx.globalAlpha = app.canvas.editor_alpha;
        ctx.restore();
    };

    const within = (pos, bounds) =>
        bounds && pos[0] >= bounds[0] && pos[0] <= bounds[0] + bounds[1];

    row.mouse = function (event, pos, node) {
        if (event.type !== "pointerdown") return false;
        if (within(pos, this.toggleBounds)) {
            boolWidget.value = !boolWidget.value;
            node.setDirtyCanvas(true, true);
            return true;
        }
        if (!boolWidget.value) return true;      // off: the share is inert
        const step = shareWidget.options?.step2 ?? shareWidget.options?.step ?? 0.05;
        const min = shareWidget.options?.min ?? -1;
        const max = shareWidget.options?.max ?? 1;
        let delta = 0;
        if (within(pos, this.decBounds)) delta = -step;
        else if (within(pos, this.incBounds)) delta = step;
        if (delta) {
            // -1 means uncapped and sits a whole step below 0; walking
            // through it rather than into it keeps the arrows monotone
            let next = shareWidget.value < 0 ? (delta > 0 ? 0 : -1)
                                             : shareWidget.value + delta;
            if (next < 0) next = -1;
            shareWidget.value = Math.min(max, Math.max(min, Number(next.toFixed(2))));
            node.setDirtyCanvas(true, true);
            return true;
        }
        // anywhere else on the row: type a value
        app.canvas.prompt("Value", shareWidget.value, (v) => {
            const parsed = Number(v);
            if (!Number.isNaN(parsed)) {
                shareWidget.value = Math.min(max, Math.max(min, parsed));
                node.setDirtyCanvas(true, true);
            }
        }, event);
        return true;
    };
    return row;
}

app.registerExtension({
    name: "alchemine.generatorPack.CategoryRows",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE) return;
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            for (const category of categoriesOf(this)) {
                const boolIndex = this.widgets?.findIndex(w => w.name === category);
                const shareIndex = this.widgets?.findIndex(
                    w => w.name === category + SHARE_SUFFIX);
                if (boolIndex === undefined || boolIndex < 0 || shareIndex < 0) continue;
                const boolWidget = this.widgets[boolIndex];
                const shareWidget = this.widgets[shareIndex];
                // hidden, not removed: it still has to serialise
                boolWidget.computeSize = () => [0, -4];
                boolWidget.draw = () => {};
                boolWidget.type = "alchemine-hidden";
                this.widgets[shareIndex] = makeRow(this, boolWidget, shareWidget);
            }
            this.setSize(this.computeSize());
            return result;
        };
    },
});
