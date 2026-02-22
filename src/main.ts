import {
	App,
	Modal,
	Notice,
	Plugin,
	PluginSettingTab,
	Setting,
	TFile,
	moment,
} from "obsidian";

type Schedule = "AM" | "PM" | "PRN";

interface MedPreset {
	label: string;
	med: string;
	dose: string;
	unit: string;
	schedule: Schedule[];
}

interface MedLogSettings {
	dailyFolder: string;
	dailyFilenameFormat: string;
	dailyTemplatePath: string;
	medMarker: string;
	vitalsMarker: string;
	enableOneClickPrnCommands: boolean;
	exportsFolder: string;
	includeSourceFileInExport: boolean;
	meds: MedPreset[];
}

const DEFAULT_MEDS: MedPreset[] = [
	{
		label: "Levothyroxine 50 mcg",
		med: "Levothyroxine",
		dose: "50",
		unit: "mcg",
		schedule: ["AM"],
	},
	{
		label: "Vitamin D3 1000 IU",
		med: "Vitamin D3",
		dose: "1000",
		unit: "IU",
		schedule: ["AM"],
	},
	{
		label: "Magnesium glycinate 200 mg",
		med: "Magnesium glycinate",
		dose: "200",
		unit: "mg",
		schedule: ["PM"],
	},
	{
		label: "Melatonin 1 mg",
		med: "Melatonin",
		dose: "1",
		unit: "mg",
		schedule: ["PM"],
	},
	{
		label: "Ibuprofen 200 mg",
		med: "Ibuprofen",
		dose: "200",
		unit: "mg",
		schedule: ["PRN"],
	},
	{
		label: "Acetaminophen 500 mg",
		med: "Acetaminophen",
		dose: "500",
		unit: "mg",
		schedule: ["PRN"],
	},
	{
		label: "Antihistamine 10 mg",
		med: "Antihistamine",
		dose: "10",
		unit: "mg",
		schedule: ["PRN"],
	},
];

const DEFAULT_SETTINGS: MedLogSettings = {
	dailyFolder: "Medical Daily",
	dailyFilenameFormat: "DD-MM-YYYY",
	dailyTemplatePath: "Templates/Medical Daily Note.md",
	medMarker: "<!-- MED_LOG -->",
	vitalsMarker: "<!-- VITALS_LOG -->",
	enableOneClickPrnCommands: true,
	exportsFolder: "exports",
	includeSourceFileInExport: true,
	meds: DEFAULT_MEDS,
};

const MED_HEADER = `| ts | med | dose | unit | hr | bp_sys | bp_dia | notes |\n|---|---|---:|---|---:|---:|---:|---|`;
const VITALS_HEADER = `| ts | hr | bp_sys | bp_dia | notes |\n|---|---:|---:|---:|---|`;

function sanitizeTsv(value: string): string {
	return value.replace(/[\t\r\n]+/g, " ").trim();
}

function parseRow(line: string, expectedCells: number): string[] | null {
	const trimmed = line.trim();
	if (!trimmed.startsWith("|")) return null;
	const cells = trimmed
		.split("|")
		.slice(1, -1)
		.map((v) => v.trim());
	if (cells.length !== expectedCells) return null;
	if (cells[0] === "ts") return null;
	if (cells[0].startsWith("---")) return null;
	return cells;
}

function parseAndValidateMeds(input: string): MedPreset[] {
	const parsed = JSON.parse(input) as unknown;
	if (!Array.isArray(parsed)) {
		throw new Error("Meds JSON must be an array.");
	}
	const validSchedules: Schedule[] = ["AM", "PM", "PRN"];
	const meds: MedPreset[] = parsed.map((item, index) => {
		if (typeof item !== "object" || item === null) {
			throw new Error(`Meds entry ${index + 1} must be an object.`);
		}
		const candidate = item as Record<string, unknown>;
		if (
			typeof candidate.label !== "string" ||
			typeof candidate.med !== "string" ||
			typeof candidate.dose !== "string" ||
			typeof candidate.unit !== "string"
		) {
			throw new Error(`Meds entry ${index + 1} must include string fields label, med, dose, unit.`);
		}
		if (!Array.isArray(candidate.schedule) || candidate.schedule.length === 0) {
			throw new Error(`Meds entry ${index + 1} must include a non-empty schedule array.`);
		}
		for (const schedule of candidate.schedule) {
			if (!validSchedules.includes(schedule as Schedule)) {
				throw new Error(`Meds entry ${index + 1} has invalid schedule value: ${String(schedule)}.`);
			}
		}
		return {
			label: candidate.label,
			med: candidate.med,
			dose: candidate.dose,
			unit: candidate.unit,
			schedule: Array.from(new Set(candidate.schedule)) as Schedule[],
		};
	});
	return meds;
}

class PrnPickerModal extends Modal {
	private readonly meds: MedPreset[];
	private readonly onChoose: (med: MedPreset) => Promise<void>;

	constructor(app: App, meds: MedPreset[], onChoose: (med: MedPreset) => Promise<void>) {
		super(app);
		this.meds = meds;
		this.onChoose = onChoose;
	}

	onOpen(): void {
		const { contentEl } = this;
		contentEl.empty();
		contentEl.createEl("h3", { text: "Select PRN medication" });
		if (this.meds.length === 0) {
			contentEl.createEl("p", { text: "No PRN medications configured." });
			return;
		}
		for (const med of this.meds) {
			const button = contentEl.createEl("button", {
				text: med.label,
				cls: "medlog-prn-button",
			});
			button.addEventListener("click", async () => {
				await this.onChoose(med);
				this.close();
			});
		}
	}

	onClose(): void {
		this.contentEl.empty();
	}
}

class VitalsModal extends Modal {
	private readonly onSubmit: (hr: string, bpSys: string, bpDia: string, notes: string) => Promise<void>;

	constructor(
		app: App,
		onSubmit: (hr: string, bpSys: string, bpDia: string, notes: string) => Promise<void>,
	) {
		super(app);
		this.onSubmit = onSubmit;
	}

	onOpen(): void {
		const { contentEl } = this;
		contentEl.empty();
		contentEl.createEl("h3", { text: "Log vitals" });

		const hrInput = contentEl.createEl("input", { type: "text" });
		hrInput.placeholder = "Heart rate";

		const bpSysInput = contentEl.createEl("input", { type: "text" });
		bpSysInput.placeholder = "BP systolic";

		const bpDiaInput = contentEl.createEl("input", { type: "text" });
		bpDiaInput.placeholder = "BP diastolic";

		const notesInput = contentEl.createEl("textarea");
		notesInput.placeholder = "Notes (optional)";

		const submit = contentEl.createEl("button", { text: "Save" });
		submit.addEventListener("click", async () => {
			await this.onSubmit(hrInput.value.trim(), bpSysInput.value.trim(), bpDiaInput.value.trim(), notesInput.value.trim());
			this.close();
		});

		const cancel = contentEl.createEl("button", { text: "Cancel" });
		cancel.addEventListener("click", () => this.close());
	}

	onClose(): void {
		this.contentEl.empty();
	}
}

export default class MedLogOneClickPlugin extends Plugin {
	settings: MedLogSettings;
	private dynamicCommandIds: string[] = [];

	async onload(): Promise<void> {
		await this.loadSettings();
		this.addSettingTab(new MedLogSettingTab(this.app, this));
		this.registerBaseCommands();
		this.refreshDynamicPrnCommands();
	}

	private registerBaseCommands(): void {
		this.addCommand({
			id: "log-am-meds",
			name: "MedLog: Log AM meds",
			callback: () => this.logScheduledMeds("AM"),
		});

		this.addCommand({
			id: "log-pm-meds",
			name: "MedLog: Log PM meds",
			callback: () => this.logScheduledMeds("PM"),
		});

		this.addCommand({
			id: "log-prn-med",
			name: "MedLog: Log PRN med…",
			callback: () => this.openPrnModal(),
		});

		this.addCommand({
			id: "log-vitals",
			name: "MedLog: Log vitals…",
			callback: () => this.openVitalsModal(),
		});

		this.addCommand({
			id: "export-tsv",
			name: "MedLog: Export TSV",
			callback: () => this.exportTsv(),
		});
	}

	refreshDynamicPrnCommands(): void {
		const allCommands = this.app.commands.commands;
		for (const id of this.dynamicCommandIds) {
			delete allCommands[id];
		}
		this.dynamicCommandIds = [];

		if (!this.settings.enableOneClickPrnCommands) {
			return;
		}
		const prnMeds = this.settings.meds.filter((med) => med.schedule.includes("PRN"));
		for (const med of prnMeds) {
			const commandId = `medlog-prn-${med.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
			if (allCommands[commandId]) {
				continue;
			}
			this.dynamicCommandIds.push(commandId);
			this.addCommand({
				id: commandId,
				name: `MedLog: PRN — ${med.label}`,
				callback: () => this.logSinglePrn(med),
			});
		}
	}

	async loadSettings(): Promise<void> {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings(): Promise<void> {
		await this.saveData(this.settings);
	}

	private nowTs(): string {
		return moment().format("DD-MM-YYYY HH:mm");
	}

	private todayFilePath(): string {
		const dailyFileName = `${moment().format(this.settings.dailyFilenameFormat)}.md`;
		return `${this.settings.dailyFolder}/${dailyFileName}`;
	}

	private fallbackDailyContent(): string {
		return `${MED_HEADER}\n${this.settings.medMarker}\n\n${VITALS_HEADER}\n${this.settings.vitalsMarker}\n`;
	}

	private async ensureFolder(path: string): Promise<void> {
		if (!path || path === "/") return;
		if (this.app.vault.getAbstractFileByPath(path)) return;
		await this.app.vault.createFolder(path);
	}

	private async ensureDailyFile(): Promise<TFile> {
		await this.ensureFolder(this.settings.dailyFolder);
		const path = this.todayFilePath();
		const existing = this.app.vault.getAbstractFileByPath(path);
		if (existing instanceof TFile) {
			return existing;
		}

		const template = this.app.vault.getAbstractFileByPath(this.settings.dailyTemplatePath);
		let content = this.fallbackDailyContent();
		if (template instanceof TFile) {
			content = await this.app.vault.cachedRead(template);
		}
		return await this.app.vault.create(path, content);
	}

	private async ensureMarkerAndHeader(file: TFile, marker: string, header: string): Promise<void> {
		let content = await this.app.vault.read(file);
		if (content.includes(marker)) return;
		if (!content.endsWith("\n")) {
			content += "\n";
		}
		content += `\n${header}\n${marker}\n`;
		await this.app.vault.modify(file, content);
	}

	private async appendRowAfterMarker(file: TFile, marker: string, row: string): Promise<void> {
		let content = await this.app.vault.read(file);
		const markerIndex = content.indexOf(marker);
		if (markerIndex === -1) {
			throw new Error(`Marker not found: ${marker}`);
		}
		const insertIndex = markerIndex + marker.length;
		const before = content.slice(0, insertIndex);
		const after = content.slice(insertIndex);
		const line = `\n${row}`;
		content = `${before}${line}${after}`;
		await this.app.vault.modify(file, content);
	}

	private async logScheduledMeds(schedule: "AM" | "PM"): Promise<void> {
		try {
			const meds = this.settings.meds.filter((med) => med.schedule.includes(schedule));
			if (meds.length === 0) {
				new Notice(`No ${schedule} meds configured.`);
				return;
			}
			const file = await this.ensureDailyFile();
			await this.ensureMarkerAndHeader(file, this.settings.medMarker, MED_HEADER);
			for (const med of meds) {
				const row = `| ${this.nowTs()} | ${med.med} | ${med.dose} | ${med.unit} |  |  |  | ${schedule} |`;
				await this.appendRowAfterMarker(file, this.settings.medMarker, row);
			}
			new Notice(`Logged ${meds.length} ${schedule} medication entr${meds.length === 1 ? "y" : "ies"}.`);
		} catch (error) {
			new Notice(`Unable to log ${schedule} meds: ${(error as Error).message}`);
		}
	}

	private async logSinglePrn(med: MedPreset): Promise<void> {
		try {
			const file = await this.ensureDailyFile();
			await this.ensureMarkerAndHeader(file, this.settings.medMarker, MED_HEADER);
			const row = `| ${this.nowTs()} | ${med.med} | ${med.dose} | ${med.unit} |  |  |  | PRN: ${med.label} |`;
			await this.appendRowAfterMarker(file, this.settings.medMarker, row);
			new Notice(`Logged PRN medication: ${med.label}.`);
		} catch (error) {
			new Notice(`Unable to log PRN med: ${(error as Error).message}`);
		}
	}

	private openPrnModal(): void {
		const prnMeds = this.settings.meds.filter((med) => med.schedule.includes("PRN"));
		new PrnPickerModal(this.app, prnMeds, async (med) => {
			await this.logSinglePrn(med);
		}).open();
	}

	private openVitalsModal(): void {
		new VitalsModal(this.app, async (hr, bpSys, bpDia, notes) => {
			if (!hr && !bpSys && !bpDia && !notes) {
				new Notice("Vitals entry cancelled.");
				return;
			}
			try {
				const file = await this.ensureDailyFile();
				await this.ensureMarkerAndHeader(file, this.settings.vitalsMarker, VITALS_HEADER);
				const row = `| ${this.nowTs()} | ${hr} | ${bpSys} | ${bpDia} | ${notes} |`;
				await this.appendRowAfterMarker(file, this.settings.vitalsMarker, row);
				new Notice("Logged vitals entry.");
			} catch (error) {
				new Notice(`Unable to log vitals: ${(error as Error).message}`);
			}
		}).open();
	}

	private extractSectionRows(content: string, marker: string, expectedCells: number): string[][] {
		const markerIndex = content.indexOf(marker);
		if (markerIndex === -1) return [];
		const tail = content.slice(markerIndex + marker.length);
		const lines = tail.split("\n").map((line) => line.trim()).filter(Boolean);
		const rows: string[][] = [];
		for (const line of lines) {
			if (!line.startsWith("|")) {
				continue;
			}
			const parsed = parseRow(line, expectedCells);
			if (parsed) {
				rows.push(parsed);
			}
		}
		return rows;
	}

	private async exportTsv(): Promise<void> {
		try {
			await this.ensureFolder(this.settings.exportsFolder);
			const dailyFolderAbstract = this.app.vault.getAbstractFileByPath(this.settings.dailyFolder);
			if (!dailyFolderAbstract) {
				new Notice("Daily folder does not exist; nothing to export.");
				return;
			}

			const files = this.app.vault
				.getMarkdownFiles()
				.filter((file) => file.path.startsWith(`${this.settings.dailyFolder}/`));

			const medsHeader = ["ts", "med", "dose", "unit", "hr", "bp_sys", "bp_dia", "notes"];
			const vitalsHeader = ["ts", "hr", "bp_sys", "bp_dia", "notes"];
			if (this.settings.includeSourceFileInExport) {
				medsHeader.push("source_file");
				vitalsHeader.push("source_file");
			}

			const medsLines: string[] = [medsHeader.join("\t")];
			const vitalsLines: string[] = [vitalsHeader.join("\t")];

			for (const file of files) {
				const content = await this.app.vault.cachedRead(file);
				for (const row of this.extractSectionRows(content, this.settings.medMarker, 8)) {
					const values = row.map(sanitizeTsv);
					if (this.settings.includeSourceFileInExport) {
						values.push(sanitizeTsv(file.path));
					}
					medsLines.push(values.join("\t"));
				}
				for (const row of this.extractSectionRows(content, this.settings.vitalsMarker, 5)) {
					const values = row.map(sanitizeTsv);
					if (this.settings.includeSourceFileInExport) {
						values.push(sanitizeTsv(file.path));
					}
					vitalsLines.push(values.join("\t"));
				}
			}

			await this.app.vault.adapter.write(`${this.settings.exportsFolder}/meds.tsv`, medsLines.join("\n"));
			await this.app.vault.adapter.write(`${this.settings.exportsFolder}/vitals.tsv`, vitalsLines.join("\n"));
			new Notice("Export complete: meds.tsv and vitals.tsv.");
		} catch (error) {
			new Notice(`Export failed: ${(error as Error).message}`);
		}
	}
}

class MedLogSettingTab extends PluginSettingTab {
	plugin: MedLogOneClickPlugin;

	constructor(app: App, plugin: MedLogOneClickPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();

		new Setting(containerEl)
			.setName("Daily folder")
			.addText((text) =>
				text.setValue(this.plugin.settings.dailyFolder).onChange(async (value) => {
					this.plugin.settings.dailyFolder = value.trim() || DEFAULT_SETTINGS.dailyFolder;
					await this.plugin.saveSettings();
				}),
			);

		new Setting(containerEl)
			.setName("Daily filename format")
			.addText((text) =>
				text.setValue(this.plugin.settings.dailyFilenameFormat).onChange(async (value) => {
					this.plugin.settings.dailyFilenameFormat = value.trim() || DEFAULT_SETTINGS.dailyFilenameFormat;
					await this.plugin.saveSettings();
				}),
			);

		new Setting(containerEl)
			.setName("Daily template path")
			.addText((text) =>
				text.setValue(this.plugin.settings.dailyTemplatePath).onChange(async (value) => {
					this.plugin.settings.dailyTemplatePath = value.trim() || DEFAULT_SETTINGS.dailyTemplatePath;
					await this.plugin.saveSettings();
				}),
			);

		new Setting(containerEl)
			.setName("Medication marker")
			.addText((text) =>
				text.setValue(this.plugin.settings.medMarker).onChange(async (value) => {
					this.plugin.settings.medMarker = value.trim() || DEFAULT_SETTINGS.medMarker;
					await this.plugin.saveSettings();
				}),
			);

		new Setting(containerEl)
			.setName("Vitals marker")
			.addText((text) =>
				text.setValue(this.plugin.settings.vitalsMarker).onChange(async (value) => {
					this.plugin.settings.vitalsMarker = value.trim() || DEFAULT_SETTINGS.vitalsMarker;
					await this.plugin.saveSettings();
				}),
			);

		new Setting(containerEl)
			.setName("Enable one-click PRN commands")
			.addToggle((toggle) =>
				toggle.setValue(this.plugin.settings.enableOneClickPrnCommands).onChange(async (value) => {
					this.plugin.settings.enableOneClickPrnCommands = value;
					await this.plugin.saveSettings();
					this.plugin.refreshDynamicPrnCommands();
				}),
			);

		new Setting(containerEl)
			.setName("Exports folder")
			.addText((text) =>
				text.setValue(this.plugin.settings.exportsFolder).onChange(async (value) => {
					this.plugin.settings.exportsFolder = value.trim() || DEFAULT_SETTINGS.exportsFolder;
					await this.plugin.saveSettings();
				}),
			);

		new Setting(containerEl)
			.setName("Include source file in export")
			.addToggle((toggle) =>
				toggle.setValue(this.plugin.settings.includeSourceFileInExport).onChange(async (value) => {
					this.plugin.settings.includeSourceFileInExport = value;
					await this.plugin.saveSettings();
				}),
			);

		new Setting(containerEl)
			.setName("Meds JSON")
			.setDesc("Array of meds with label, med, dose, unit, schedule.")
			.addTextArea((text) => {
				text.inputEl.rows = 14;
				text.inputEl.cols = 60;
				text.setValue(JSON.stringify(this.plugin.settings.meds, null, 2));
				text.onChange(async (value) => {
					try {
						const meds = parseAndValidateMeds(value);
						this.plugin.settings.meds = meds;
						await this.plugin.saveSettings();
						this.plugin.refreshDynamicPrnCommands();
					} catch (error) {
						new Notice(`Invalid meds JSON: ${(error as Error).message}`);
					}
				});
			});
	}
}
