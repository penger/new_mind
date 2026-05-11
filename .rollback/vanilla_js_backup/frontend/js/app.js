// ==========================================
// 配置与初始化
// API_BASE_URL 使用相对路径，通过 nginx 反向代理
// ==========================================
const API_BASE_URL = '/api';

class GraphEditor {
    constructor() {
        this.nodes = [];
        this.links = [];
        this.nodeIdCounter = 1;
        this.linkIdCounter = 1;

        this.nodeStyles = [];
        this.edgeStyles = [];
        this.themes = [];
        this.resourceIdCounter = 1;

        this.visibleThemes = new Set();
        this.activeThemeFilter = null;  // 单选的图层过滤
        this.activeCreateThemeId = null;

        this.mode = 'view';
        this.currentTransform = d3.zoomIdentity;
        this.isBrushing = false;
        this.brushStartPoint = null;
        this.isLinking = false;
        this.linkSourceNode = null;
        this.hoveredNode = null;

        this.editingItem = null;
        this.editingType = null;

        this.rmActiveTab = 'themes';
        this.rmEditingId = null;

        this.isSaving = false;

        this.initD3();
        this.initEvents();

        this.fetchDataFromServer();
    }

    // ==========================================
    // 接口联调模块 (API Data Sync)
    // ==========================================
    async fetchDataFromServer() {
        try {
            const response = await fetch(`${API_BASE_URL}/data`);
            if (!response.ok) throw new Error("图谱未找到或网络错误");

            const data = await response.json();

            this.nodeStyles = data.nodeStyles || [];
            this.edgeStyles = data.edgeStyles || [];
            this.themes = data.themes || [];
            this.nodes = data.nodes || [];
            this.links = data.links || [];

            if (this.themes.length === 0) {
                await this.initDefaultData();
            }

            this.syncCounters();
            // 按 id 排序
            this.themes.sort((a, b) => a.id.localeCompare(b.id));
            this.visibleThemes = new Set(this.themes.map(t => t.id));
            this.activeThemeFilter = this.themes[0]?.id || null;
            this.activeCreateThemeId = this.themes[0]?.id || null;

            this.showToast("从数据库加载数据成功！");
        } catch (error) {
            console.error("Fetch error:", error);
            this.showToast("未找到数据，初始化新图谱...");
            await this.initDefaultData();
        }

        d3.select("#statusInfo").text("可自由缩放和平移");
        this.updateAllSelects();
        this.render();
    }

    async initDefaultData() {
        // 初始化默认样式和主题
        this.nodeStyles = [
            { id: 'NS1', name: '默认节点', color: '#3498db', shape: 'circle', opacity: 1 }
        ];
        this.edgeStyles = [
            { id: 'ES1', name: '默认连线', color: '#95a5a6', style: 'solid' }
        ];
        this.themes = [
            { id: 'T1', name: '默认主题', defaultNodeStyleId: 'NS1', defaultEdgeStyleId: 'ES1' }
        ];
        this.nodes = [];
        this.links = [];
        this.resourceIdCounter = 2;
        this.visibleThemes = new Set(['T1']);
        this.activeThemeFilter = 'T1';
        this.activeCreateThemeId = 'T1';

        await this.saveToDatabase();
    }

    syncCounters() {
        if (this.nodes.length) this.nodeIdCounter = Math.max(...this.nodes.map(n => parseInt(n.id.replace('N',''))||0)) + 1;
        if (this.links.length) this.linkIdCounter = Math.max(...this.links.map(l => parseInt(l.id.replace('E',''))||0)) + 1;
        const maxResourceId = Math.max(
            ...this.themes.map(t => parseInt(t.id.replace('T',''))||0),
            ...this.nodeStyles.map(ns => parseInt(ns.id.replace('NS',''))||0),
            ...this.edgeStyles.map(es => parseInt(es.id.replace('ES',''))||0)
        );
        this.resourceIdCounter = maxResourceId + 1;
    }

    async saveToDatabase() {
        if (this.isSaving) return;
        this.isSaving = true;

        const payload = {
            themes: this.themes.map(t => ({
                id: t.id,
                name: t.name,
                defaultNodeStyleId: t.defaultNodeStyleId,
                defaultEdgeStyleId: t.defaultEdgeStyleId
            })),
            nodeStyles: this.nodeStyles.map(ns => ({
                id: ns.id, name: ns.name, color: ns.color, shape: ns.shape, opacity: ns.opacity
            })),
            edgeStyles: this.edgeStyles.map(es => ({
                id: es.id, name: es.name, color: es.color, style: es.style
            })),
            nodes: this.nodes.map(n => ({
                id: n.id, label: n.label, size: n.size, themeId: n.themeId, nodeStyleId: n.nodeStyleId
            })),
            links: this.links.map(l => ({
                id: l.id,
                source: typeof l.source === 'object' ? l.source.id : l.source,
                target: typeof l.target === 'object' ? l.target.id : l.target,
                label: l.label, width: l.width, themeId: l.themeId, edgeStyleId: l.edgeStyleId
            }))
        };

        try {
            const response = await fetch(`${API_BASE_URL}/data`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                console.error("保存失败:", err);
            }
        } catch(err) {
            console.error("网络错误:", err);
        } finally {
            this.isSaving = false;
        }
    }

    // ==========================================
    // 工具与 UI 模块
    // ==========================================
    showToast(msg, duration = 2000) {
        const toast = d3.select("#toast");
        toast.text(msg).style("opacity", 1);
        setTimeout(() => toast.style("opacity", 0), duration);
    }

    asyncConfirm(msg) {
        return new Promise(resolve => {
            d3.select("#confirmMsg").text(msg);
            d3.select("#confirmDialog").style("display", "flex");
            d3.select("#confirmOk").on("click", () => { d3.select("#confirmDialog").style("display", "none"); resolve(true); });
            d3.select("#confirmCancel").on("click", () => { d3.select("#confirmDialog").style("display", "none"); resolve(false); });
        });
    }

    initD3() {
        this.svg = d3.select("#graph-svg");
        this.mainG = d3.select("#main-group");

        this.zoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .filter(event => !event.shiftKey && event.type !== 'dblclick')
            .on("zoom", (event) => {
                this.currentTransform = event.transform;
                this.mainG.attr("transform", event.transform);
            });
        this.svg.call(this.zoom);

        this.simulation = d3.forceSimulation()
            .alphaDecay(0.05)
            .velocityDecay(0.6)
            .force("link", d3.forceLink().id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(this.svg.node().clientWidth / 2, this.svg.node().clientHeight / 2))
            .force("collision", d3.forceCollide().radius(35));
    }

    initEvents() {
        d3.selectAll('input[name="mode"]').on("change", (e) => this.setMode(e.target.value));

        this.svg.on("mousedown", (event) => {
            if (this.mode !== 'edit') return;
            if (event.shiftKey && event.target.id === 'graph-svg') {
                this.isBrushing = true;
                this.brushStartPoint = d3.pointer(event, this.svg.node());
                d3.select("#selection-box").style("display", "block")
                    .attr("x", this.brushStartPoint[0]).attr("y", this.brushStartPoint[1])
                    .attr("width", 0).attr("height", 0);
            } else if (event.target.id === 'graph-svg') {
                this.clearSelection();
                this.closeProperties();
            }
        });

        this.svg.on("mousemove", (event) => {
            if (this.mode !== 'edit' || !this.isBrushing) return;
            const currentPos = d3.pointer(event, this.svg.node());
            const x = Math.min(this.brushStartPoint[0], currentPos[0]);
            const y = Math.min(this.brushStartPoint[1], currentPos[1]);
            const w = Math.abs(currentPos[0] - this.brushStartPoint[0]);
            const h = Math.abs(currentPos[1] - this.brushStartPoint[1]);
            d3.select("#selection-box").attr("x", x).attr("y", y).attr("width", w).attr("height", h);

            const p1 = this.currentTransform.invert([x, y]);
            const p2 = this.currentTransform.invert([x+w, y+h]);

            this.nodes.forEach(n => {
                if (this.visibleThemes.has(n.themeId)) {
                    n.selected = (n.x >= p1[0] && n.x <= p2[0] && n.y >= p1[1] && n.y <= p2[1]);
                }
            });
            this.render();
        });

        window.addEventListener("mouseup", () => {
            if (this.isBrushing) { this.isBrushing = false; d3.select("#selection-box").style("display", "none"); }
            if (this.isLinking) {
                this.isLinking = false; d3.select("#ghost-line").style("display", "none");
                this.linkSourceNode = null;
            }
        });

        this.svg.on("dblclick", (event) => {
            if (this.mode === 'edit' && event.target.id === 'graph-svg') {
                const [x, y] = this.currentTransform.invert(d3.pointer(event));
                this.addNode(x, y);
            }
        });

        d3.select("body").on("keydown", (event) => {
            if (this.mode === 'edit' && (event.key === "Delete" || event.key === "Backspace")) {
                if (event.target.tagName !== "INPUT" && event.target.tagName !== "SELECT") {
                    this.deleteSelected();
                }
            }
        });

        d3.select("#propertiesForm").on("submit", (e) => { e.preventDefault(); this.saveProperties(); });
        d3.select("#rmForm").on("submit", (e) => { e.preventDefault(); this.rmSave(); });
    }

    updateAllSelects() {
        this.populateSelect("#themeFilter", this.themes, this.activeThemeFilter, (e) => {
            this.activeThemeFilter = e.target.value;
            this.visibleThemes = new Set([this.activeThemeFilter]);
            this.render();
        });
        this.populateSelect("#defaultCreateTheme", this.themes, this.activeCreateThemeId, (e) => { this.activeCreateThemeId = e.target.value; });
        this.populateSelect("#propTheme", this.themes);
        this.populateSelect("#propNodeStyle", this.nodeStyles);
        this.populateSelect("#propEdgeStyle", this.edgeStyles);
        this.populateSelect("#rmThemeNodeStyle", this.nodeStyles);
        this.populateSelect("#rmThemeEdgeStyle", this.edgeStyles);
    }

    populateSelect(selector, dataArray, selectedValue = null, onChange = null) {
        const el = d3.select(selector);
        el.selectAll("*").remove();
        dataArray.forEach(item => {
            el.append("option").attr("value", item.id).text(item.name);
        });
        if(selectedValue) el.node().value = selectedValue;
        if(onChange) el.on("change", onChange);
    }

    // ==========================================
    // 画布交互与渲染
    // ==========================================
    setMode(newMode) {
        this.mode = newMode;
        const status = d3.select("#statusInfo");
        if (this.mode === 'edit') {
            this.nodes.forEach(n => { n.fx = n.x; n.fy = n.y; n.vx = 0; n.vy = 0; });
            this.simulation.alpha(0).stop();
            status.text("✏️ 编辑模式: 双击添加节点，Shift+拖拽连线");
            this.svg.style("cursor", "crosshair");
        } else {
            this.nodes.forEach(n => { n.fx = null; n.fy = null; });
            this.clearSelection();
            this.closeProperties();
            this.simulation.alpha(1).restart();
            status.text("👁️ 浏览模式: 布局自动调整中，可自由缩放和平移");
            this.svg.style("cursor", "grab");
        }
        this.render();
    }

    async addNode(x, y) {
        const theme = this.themes.find(t => t.id === this.activeCreateThemeId) || this.themes[0];
        const nodeStyle = theme.defaultNodeStyleId ? this.nodeStyles.find(s => s.id === theme.defaultNodeStyleId) : this.nodeStyles[0];
        const newNode = {
            id: `N${this.nodeIdCounter++}`, label: `节点${this.nodeIdCounter - 1}`, x: x, y: y,
            themeId: theme.id, nodeStyleId: nodeStyle?.id || this.nodeStyles[0]?.id, size: 22, selected: true
        };
        if (this.mode === 'edit') { newNode.fx = x; newNode.fy = y; }
        this.clearSelection();
        this.nodes.push(newNode);
        if(!this.visibleThemes.has(theme.id)) {
            this.visibleThemes.add(theme.id);
            this.activeThemeFilter = theme.id;
            this.updateAllSelects();
        }
        this.render();
        if(this.mode === 'edit') this.manualTick();
        await this.saveToDatabase();
    }

    async addEdge(source, target) {
        if (source === target) return;
        const sid = source.id || source, tid = target.id || target;
        if (this.links.find(l => {
            const lsid = l.source.id || l.source;
            const ltid = l.target.id || l.target;
            return (lsid === sid && ltid === tid) || (lsid === tid && ltid === sid);
        })) return;

        const theme = this.themes.find(t => t.id === this.activeCreateThemeId) || this.themes[0];
        const edgeStyle = theme.defaultEdgeStyleId ? this.edgeStyles.find(s => s.id === theme.defaultEdgeStyleId) : this.edgeStyles[0];
        const newLink = {
            id: `E${this.linkIdCounter++}`, source: source, target: target, label: "", width: 2,
            themeId: theme.id, edgeStyleId: edgeStyle?.id || this.edgeStyles[0]?.id, selected: false
        };
        this.links.push(newLink);
        this.render();
        if(this.mode === 'edit') this.manualTick();
        await this.saveToDatabase();
    }

    getNodeStyle(id) { return this.nodeStyles.find(s => s.id === id) || this.nodeStyles[0]; }
    getEdgeStyle(id) { return this.edgeStyles.find(s => s.id === id) || this.edgeStyles[0]; }

    getSymbolGenerator(shape, size) {
        let type;
        switch(shape) {
            case 'square': type = d3.symbolSquare; break;
            case 'triangle': type = d3.symbolTriangle; break;
            case 'star': type = d3.symbolStar; break;
            case 'diamond': type = d3.symbolDiamond; break;
            case 'circle': default: type = d3.symbolCircle;
        }
        return d3.symbol().type(type).size(size * size * 3.14)();
    }

    render() {
        const self = this;

        const link = this.mainG.select("#links-group").selectAll(".link").data(this.links, d => d.id);
        link.exit().remove();
        const linkEnter = link.enter().append("line")
            .attr("class", "link").attr("marker-end", "url(#arrowhead)")
            .on("click", (e, d) => {
                if (self.mode === 'edit') { e.stopPropagation(); if (!e.shiftKey) self.clearSelection(); d.selected = true; self.render(); }
            })
            .on("dblclick", (e, d) => { if (self.mode === 'edit') { e.stopPropagation(); self.openProperties(d, 'edge'); } });

        const linkCombined = linkEnter.merge(link)
            .attr("stroke", d => self.getEdgeStyle(d.edgeStyleId)?.color || '#95a5a6')
            .attr("stroke-width", d => d.width)
            .attr("stroke-dasharray", d => self.getEdgeStyle(d.edgeStyleId)?.style === 'dashed' ? "6,6" : "none")
            .classed("selected", d => d.selected)
            .attr("marker-end", d => d.selected ? "url(#arrowhead-selected)" : "url(#arrowhead)")
            .style("display", d => {
                const sTheme = (typeof d.source === 'object') ? d.source.themeId : (self.nodes.find(n=>n.id===d.source)?.themeId);
                const tTheme = (typeof d.target === 'object') ? d.target.themeId : (self.nodes.find(n=>n.id===d.target)?.themeId);
                return (self.visibleThemes.has(sTheme) && self.visibleThemes.has(tTheme)) ? "block" : "none";
            });

        const nodeDrag = d3.drag()
            .filter(event => self.mode === 'edit')
            .on("start", function(event, d) {
                if (event.sourceEvent.shiftKey) { self.isLinking = true; self.linkSourceNode = d; }
                else { if (!d.selected) { self.clearSelection(); d.selected = true; self.render(); } }
            })
            .on("drag", function(event, d) {
                if (self.isLinking) {
                    d3.select("#ghost-line").style("display", "block").attr("x1", self.linkSourceNode.x).attr("y1", self.linkSourceNode.y).attr("x2", event.x).attr("y2", event.y);
                } else {
                    const dx = event.dx / self.currentTransform.k, dy = event.dy / self.currentTransform.k;
                    self.nodes.filter(n => n.selected).forEach(n => { n.x += dx; n.y += dy; n.fx = n.x; n.fy = n.y; });
                    self.manualTick();
                }
            })
            .on("end", function(event, d) {
                if (self.isLinking) {
                    self.isLinking = false; d3.select("#ghost-line").style("display", "none");
                    if (self.hoveredNode && self.hoveredNode !== self.linkSourceNode) self.addEdge(self.linkSourceNode, self.hoveredNode);
                    self.linkSourceNode = null;
                } else {
                    self.saveToDatabase();
                }
            });

        const node = this.mainG.select("#nodes-group").selectAll(".node").data(this.nodes, d => d.id);
        node.exit().remove();
        const nodeEnter = node.enter().append("path")
            .attr("class", "node").call(nodeDrag)
            .on("click", (e, d) => {
                if (self.mode === 'edit') { e.stopPropagation(); if (!e.shiftKey) self.clearSelection(); d.selected = true; self.render(); }
            })
            .on("dblclick", (e, d) => { if (self.mode === 'edit') { e.stopPropagation(); self.openProperties(d, 'node'); } })
            .on("mouseover", (e, d) => {
                self.hoveredNode = d;
                const tName = (self.themes.find(t=>t.id===d.themeId)||{}).name || '未知';
                const sName = self.getNodeStyle(d.nodeStyleId)?.name || '未知';
                d3.select("#tooltip").style("opacity", 1).html(`${d.label}<br/><small>[${tName}] - ${sName}</small>`)
                    .style("left", (e.pageX + 10)+"px").style("top", (e.pageY - 35)+"px");
            })
            .on("mouseout", () => { self.hoveredNode = null; d3.select("#tooltip").style("opacity", 0); });

        const nodeCombined = nodeEnter.merge(node)
            .attr("d", d => self.getSymbolGenerator(self.getNodeStyle(d.nodeStyleId)?.shape || 'circle', d.size))
            .attr("fill", d => self.getNodeStyle(d.nodeStyleId)?.color || '#3498db')
            .attr("opacity", d => self.getNodeStyle(d.nodeStyleId)?.opacity || 1)
            .classed("selected", d => d.selected)
            .style("display", d => self.visibleThemes.has(d.themeId) ? "block" : "none");

        const nodeLabels = this.mainG.select("#labels-group").selectAll(".node-label").data(this.nodes, d => d.id);
        nodeLabels.exit().remove();
        const nodeLabelsCombined = nodeLabels.enter().append("text")
            .attr("class", "node-label").attr("text-anchor", "middle").merge(nodeLabels).text(d => d.label)
            .style("display", d => self.visibleThemes.has(d.themeId) ? "block" : "none");

        if (this.mode === 'view') {
            this.simulation.nodes(this.nodes);
            this.simulation.force("link").links(this.links);
            this.simulation.on("tick", () => this.updatePositions(linkCombined, nodeCombined, nodeLabelsCombined));
            this.simulation.alpha(1).restart();
        } else {
            this.updatePositions(linkCombined, nodeCombined, nodeLabelsCombined);
        }

        this.updateSelectionSidebar();
        if (this.editingItem && !this.editingItem.selected) this.closeProperties();
    }

    updatePositions(links, nodes, labels) {
        links.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        nodes.attr("transform", d => `translate(${d.x}, ${d.y})`);
        labels.attr("x", d => d.x).attr("y", d => d.y - (d.size + 8));
    }

    manualTick() { this.updatePositions(this.mainG.selectAll(".link"), this.mainG.selectAll(".node"), this.mainG.selectAll(".node-label")); }

    // ==========================================
    // 属性分配与资源库面板
    // ==========================================
    openProperties(item, type) {
        this.editingItem = item;
        this.editingType = type;
        if(!item.selected) { this.clearSelection(); item.selected = true; this.render(); }

        d3.select("#propertiesPanel").classed("open", true);
        d3.select("#propLabel").node().value = item.label;
        d3.select("#propTheme").node().value = item.themeId || this.activeCreateThemeId;

        if (type === 'node') {
            d3.select("#propNodeFields").style("display", "block"); d3.select("#propEdgeFields").style("display", "none");
            d3.select("#propNodeStyle").node().value = item.nodeStyleId;
        } else {
            d3.select("#propNodeFields").style("display", "none"); d3.select("#propEdgeFields").style("display", "block");
            d3.select("#propEdgeStyle").node().value = item.edgeStyleId;
        }
    }

    async saveProperties() {
        if (!this.editingItem) return;
        this.editingItem.label = d3.select("#propLabel").node().value;
        this.editingItem.themeId = d3.select("#propTheme").node().value;
        if (this.editingType === 'node') this.editingItem.nodeStyleId = d3.select("#propNodeStyle").node().value;
        else this.editingItem.edgeStyleId = d3.select("#propEdgeStyle").node().value;
        this.render();
        await this.saveToDatabase();
    }

    closeProperties() { d3.select("#propertiesPanel").classed("open", false); this.editingItem = null; }

    openResourceManager() { d3.select("#resourceManagerModal").style("display", "flex"); this.rmSwitchTab('themes'); }
    closeResourceManager() { d3.select("#resourceManagerModal").style("display", "none"); this.updateAllSelects(); this.render(); }

    rmSwitchTab(tabName) {
        this.rmActiveTab = tabName;
        d3.selectAll(".modal-tab").classed("active", false); d3.select(`.modal-tab[data-tab="${tabName}"]`).classed("active", true);
        d3.select("#formThemes").style("display", tabName === 'themes' ? "block" : "none");
        d3.select("#formNodeStyles").style("display", tabName === 'nodeStyles' ? "block" : "none");
        d3.select("#formEdgeStyles").style("display", tabName === 'edgeStyles' ? "block" : "none");
        this.rmRenderList();
        const list = this.getListData();
        if(list.length > 0) this.rmSelectItem(list[0].id); else d3.select("#rmEditPane").style("display", "none");
    }

    getListData() { return this.rmActiveTab === 'themes' ? this.themes : (this.rmActiveTab === 'nodeStyles' ? this.nodeStyles : this.edgeStyles); }

    rmRenderList() {
        const list = d3.select("#rmList"); list.selectAll("*").remove();
        this.getListData().forEach(item => {
            const el = list.append("div").attr("class", `tm-item ${item.id === this.rmEditingId ? 'active' : ''}`).on("click", () => this.rmSelectItem(item.id));
            let color = '#ccc';
            if(this.rmActiveTab === 'themes') color = this.getNodeStyle(item.defaultNodeStyleId)?.color || '#ccc';
            else color = item.color || '#ccc';
            el.append("div").attr("class", "tm-color-dot").style("background", color);
            el.append("span").text(item.name);
        });
    }

    rmSelectItem(id) {
        this.rmEditingId = id; this.rmRenderList(); d3.select("#rmEditPane").style("display", "block");
        const item = this.getListData().find(x => x.id === id);
        if(!item) return;
        d3.select("#rmName").node().value = item.name;

        if (this.rmActiveTab === 'themes') {
            d3.select("#rmThemeNodeStyle").node().value = item.defaultNodeStyleId || '';
            d3.select("#rmThemeEdgeStyle").node().value = item.defaultEdgeStyleId || '';
        } else if (this.rmActiveTab === 'nodeStyles') {
            d3.select("#rmNodeColor").node().value = item.color || '#3498db';
            d3.select("#rmNodeShape").node().value = item.shape || 'circle';
            d3.select("#rmNodeOpacity").node().value = item.opacity || 1;
        } else {
            d3.select("#rmEdgeColor").node().value = item.color || '#95a5a6';
            d3.select("#rmEdgeStyle").node().value = item.style || 'solid';
        }
    }

    rmCreateNew() {
        let newItem;
        if (this.rmActiveTab === 'themes') {
            newItem = { id: `T${this.resourceIdCounter++}`, name: '新主题', defaultNodeStyleId: this.nodeStyles[0]?.id, defaultEdgeStyleId: this.edgeStyles[0]?.id };
            this.themes.push(newItem);
            this.themes.sort((a, b) => a.id.localeCompare(b.id));
            this.visibleThemes.add(newItem.id);
        } else if (this.rmActiveTab === 'nodeStyles') {
            newItem = { id: `NS${this.resourceIdCounter++}`, name: '新节点样式', color: '#9b59b6', shape: 'circle', opacity: 1 };
            this.nodeStyles.push(newItem);
        } else {
            newItem = { id: `ES${this.resourceIdCounter++}`, name: '新连线样式', color: '#95a5a6', style: 'solid' };
            this.edgeStyles.push(newItem);
        }
        this.updateAllSelects(); this.rmSelectItem(newItem.id);
    }

    async rmSave() {
        if(!this.rmEditingId) return;
        const item = this.getListData().find(x => x.id === this.rmEditingId);
        item.name = d3.select("#rmName").node().value;
        if (this.rmActiveTab === 'themes') {
            item.defaultNodeStyleId = d3.select("#rmThemeNodeStyle").node().value;
            item.defaultEdgeStyleId = d3.select("#rmThemeEdgeStyle").node().value;
        } else if (this.rmActiveTab === 'nodeStyles') {
            item.color = d3.select("#rmNodeColor").node().value;
            item.shape = d3.select("#rmNodeShape").node().value;
            item.opacity = parseFloat(d3.select("#rmNodeOpacity").node().value);
        } else {
            item.color = d3.select("#rmEdgeColor").node().value;
            item.style = d3.select("#rmEdgeStyle").node().value;
        }
        this.rmRenderList(); this.updateAllSelects(); this.render();
        await this.saveToDatabase();
        this.showToast("已保存到数据库");
    }

    async rmDeleteCurrent() {
        const data = this.getListData();
        if(data.length <= 1) { this.showToast("该类别下必须保留至少一个选项！"); return; }
        const confirmed = await this.asyncConfirm("确定要删除此项吗？相关引用会被重置！");
        if(!confirmed) return;

        if (this.rmActiveTab === 'themes') {
            this.themes = this.themes.filter(x => x.id !== this.rmEditingId);
            this.nodes.forEach(n => { if(n.themeId === this.rmEditingId) n.themeId = this.themes[0].id; });
            this.links.forEach(l => { if(l.themeId === this.rmEditingId) l.themeId = this.themes[0].id; });
            this.visibleThemes.delete(this.rmEditingId);
            if(this.activeThemeFilter === this.rmEditingId) this.activeThemeFilter = this.themes[0].id;
            if(this.activeCreateThemeId === this.rmEditingId) this.activeCreateThemeId = this.themes[0].id;
        } else if (this.rmActiveTab === 'nodeStyles') {
            this.nodeStyles = this.nodeStyles.filter(x => x.id !== this.rmEditingId);
            this.nodes.forEach(n => { if(n.nodeStyleId === this.rmEditingId) n.nodeStyleId = this.nodeStyles[0].id; });
            this.themes.forEach(t => { if(t.defaultNodeStyleId === this.rmEditingId) t.defaultNodeStyleId = this.nodeStyles[0].id; });
        } else {
            this.edgeStyles = this.edgeStyles.filter(x => x.id !== this.rmEditingId);
            this.links.forEach(l => { if(l.edgeStyleId === this.rmEditingId) l.edgeStyleId = this.edgeStyles[0].id; });
            this.themes.forEach(t => { if(t.defaultEdgeStyleId === this.rmEditingId) t.defaultEdgeStyleId = this.edgeStyles[0].id; });
        }
        this.updateAllSelects();
        if (this.getListData().length > 0) this.rmSelectItem(this.getListData()[0].id);
        this.render();
        await this.saveToDatabase();
    }

    // ==========================================
    // 其他操作
    // ==========================================
    clearSelection() { this.nodes.forEach(n => n.selected = false); this.links.forEach(l => l.selected = false); this.render(); }

    async deleteSelected() {
        if(this.mode !== 'edit') return;
        const selectedNodes = this.nodes.filter(n => n.selected).map(n => n.id);
        this.nodes = this.nodes.filter(n => !n.selected);
        this.links = this.links.filter(l => {
            const sid = l.source.id || l.source;
            const tid = l.target.id || l.target;
            return !l.selected && !selectedNodes.includes(sid) && !selectedNodes.includes(tid);
        });
        this.closeProperties(); this.render();
        if(this.mode === 'edit') this.manualTick();
        await this.saveToDatabase();
    }

    updateSelectionSidebar() {
        const list = d3.select("#selectionList"); list.selectAll("*").remove();
        const selectedNodes = this.nodes.filter(n => n.selected && this.visibleThemes.has(n.themeId));
        const selectedLinks = this.links.filter(l => {
            const sTheme = (typeof l.source === 'object') ? l.source.themeId : (this.nodes.find(n=>n.id===l.source)?.themeId);
            const tTheme = (typeof l.target === 'object') ? l.target.themeId : (this.nodes.find(n=>n.id===l.target)?.themeId);
            return l.selected && this.visibleThemes.has(sTheme) && this.visibleThemes.has(tTheme);
        });

        if (selectedNodes.length === 0 && selectedLinks.length === 0) { list.append("div").style("color", "#aaa").style("font-size", "0.85rem").text("当前无选中项"); return; }
        selectedNodes.forEach(n => { const style = this.getNodeStyle(n.nodeStyleId); list.append("div").attr("class", "list-card").html(`<span style="color:${style?.color || '#ccc'}">●</span> ${n.label}`); });
        selectedLinks.forEach(l => {
            const sLabel = (typeof l.source === 'object') ? l.source.label : (this.nodes.find(n=>n.id===l.source)?.label || '节点');
            const tLabel = (typeof l.target === 'object') ? l.target.label : (this.nodes.find(n=>n.id===l.target)?.label || '节点');
            list.append("div").attr("class", "list-card").html(`➖ ${sLabel} ➝ ${tLabel}`);
        });
    }
}

const editor = new GraphEditor();
