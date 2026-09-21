import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  Activity,
  ArrowRight,
  ChevronDown,
  ClipboardList,
  ExternalLink,
  FileText,
  FlaskConical,
  HeartPulse,
  Info,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { empty, example, fields, groups, labels } from "./fields";
import type { Analysis } from "./fields";

export default function App() {
  const [values, setValues] = useState({ ...empty });
  const [result, setResult] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [isExample, setIsExample] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const abort = useRef<AbortController | null>(null);
  const resultsRef = useRef<HTMLElement | null>(null);
  useEffect(() => () => abort.current?.abort(), []);
  const change = (key: string, value: string) => {
    setValues((v) => ({ ...v, [key]: value }));
    setResult(null);
    setError("");
    setIsExample(false);
  };
  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    const controller = new AbortController();
    abort.current = controller;
    const timer = setTimeout(() => controller.abort(), 20000);
    try {
      const patient = Object.fromEntries(
        fields.map((f) => [
          f.key,
          values[f.key] === "" ? null : Number(values[f.key]),
        ]),
      );
      const response = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patient),
        signal: controller.signal,
      });
      if (!response.ok) {
        let message = "Analysis failed. Check the connection and try again.";
        try {
          const body = await response.json();
          message = Array.isArray(body.detail)
            ? body.detail
                .map(
                  (d: { loc: string[]; msg: string }) =>
                    `${labels[d.loc.at(-1) || ""] || "Input"}: ${d.msg}`,
                )
                .join("; ")
            : body.detail || message;
        } catch {
          /* keep useful default */
        }
        throw Error(message);
      }
      const body: Analysis = await response.json();
      setResult(body);
      requestAnimationFrame(() => {
        resultsRef.current?.focus({ preventScroll: true });
        resultsRef.current?.scrollIntoView({
          block: "start",
          behavior: "instant",
        });
      });
    } catch (e) {
      setError(
        e instanceof Error
          ? e.name === "AbortError"
            ? "The request timed out. Try again when the service is ready."
            : e instanceof TypeError
              ? "Could not reach the analysis service. Please try again."
              : e.message
          : "Could not reach the analysis service.",
      );
    } finally {
      clearTimeout(timer);
      setBusy(false);
      abort.current = null;
    }
  }
  const probability = result ? result.prediction.disease_probability * 100 : 0;
  const contributions = result
    ? [...result.prediction.contributions]
        .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
        .slice(0, showAll ? 13 : 6)
        .map((c) => ({
          ...c,
          label: labels[c.feature],
          points: Number((c.shap_value * 100).toFixed(2)),
        }))
    : [];
  return (
    <>
      <a className="skip-link" href="#patient-form">
        Skip to patient intake
      </a>
      <header className="app-header">
        <a className="brand" href="/" aria-label="AegisHealth home">
          <span className="brand-mark">
            <HeartPulse size={23} />
          </span>
          <span>
            Aegis<span className="brand-light">Health</span>
          </span>
        </a>
        <div className="header-divider" />
        <span className="header-label">Clinical decision support</span>
      </header>
      <main className="workspace">
        <div className="page-heading">
          <div>
            <h1>Cardiovascular assessment</h1>
            <p className="subtitle">
              Enter patient measurements to review the estimate and supporting
              evidence.
            </p>
          </div>
        </div>
        <div className="workspace-grid">
          <aside className="intake panel">
            <div className="panel-top">
              <div className="title-with-icon">
                <ClipboardList size={19} />
                <h2>Patient details</h2>
              </div>
            </div>
            <div className="intake-caption">
              <span>
                {isExample ? "Example data" : "Enter measurements below"}
              </span>
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  setValues({ ...example });
                  setResult(null);
                  setError("");
                  setIsExample(true);
                }}
              >
                Load example
              </button>
            </div>
            <form id="patient-form" onSubmit={analyze}>
              <fieldset disabled={busy} className="all-fields">
                {groups.map((group) => (
                  <fieldset className="field-group" key={group.title}>
                    <legend>{group.title}</legend>
                    <p className="field-note">{group.note}</p>
                    <div className="field-grid">
                      {group.fields.map((field) => (
                        <label
                          className={
                            field.options ? "field field-wide" : "field"
                          }
                          key={field.key}
                          htmlFor={field.key}
                        >
                          <span>{field.label}</span>
                          {field.options ? (
                            <div className="select-wrap">
                              <select
                                id={field.key}
                                name={field.key}
                                value={values[field.key]}
                                required={!field.optional}
                                onChange={(e) =>
                                  change(field.key, e.target.value)
                                }
                              >
                                <option value="">
                                  {field.optional
                                    ? "Unknown"
                                    : "Select a result"}
                                </option>
                                {field.options.map(([value, label]) => (
                                  <option key={value} value={value}>
                                    {label}
                                  </option>
                                ))}
                              </select>
                              <ChevronDown size={14} />
                            </div>
                          ) : (
                            <div className="input-wrap">
                              <input
                                id={field.key}
                                name={field.key}
                                type="number"
                                value={values[field.key]}
                                min={field.min}
                                max={field.max}
                                step={field.step || "any"}
                                required
                                onChange={(e) =>
                                  change(field.key, e.target.value)
                                }
                                placeholder="—"
                              />
                              <span>{field.unit}</span>
                            </div>
                          )}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                ))}
              </fieldset>
              <div className="form-actions">
                {error && (
                  <p role="alert" className="error-message">
                    {error}
                  </p>
                )}
                <button
                  className="primary-button"
                  type="submit"
                  disabled={busy}
                >
                  {busy ? (
                    <LoaderCircle className="spin" size={18} />
                  ) : (
                    <Activity size={18} />
                  )}{" "}
                  {busy ? "Analyzing case…" : "Analyze case"}
                  {!busy && <ArrowRight size={17} />}
                </button>
                <button
                  className="reset-button"
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    setValues({ ...empty });
                    setResult(null);
                    setError("");
                    setIsExample(false);
                  }}
                >
                  <RotateCcw size={13} /> Clear measurements
                </button>
                <p className="privacy-note">
                  Use example or consented data. Measurements may be sent to an
                  AI provider to generate a summary.
                </p>
              </div>
            </form>
          </aside>
          <section
            className="results"
            ref={resultsRef}
            tabIndex={-1}
            aria-label="Analysis results"
          >
            <div className="results-heading">
              <div className="flex items-center gap-2">
                <span className="small-rule" />
                <h2>Assessment results</h2>
              </div>
              <span className="result-state" aria-live="polite">
                {busy
                  ? "Analyzing…"
                  : result
                    ? result.status === "complete"
                      ? "Complete"
                      : "Summary unavailable"
                    : "Not yet analyzed"}
              </span>
            </div>
            <div className="overview-grid">
              <article className="panel probability-panel">
                <h3>Disease probability</h3>
                <div
                  className="gauge-wrap"
                  role="img"
                  aria-label={
                    result
                      ? `Model probability ${probability.toFixed(1)} percent`
                      : "Probability gauge awaiting analysis"
                  }
                >
                  <ResponsiveContainer width="100%" height={178}>
                    <RadialBarChart
                      innerRadius="82%"
                      outerRadius="100%"
                      data={[{ value: probability }]}
                      startAngle={180}
                      endAngle={0}
                      cx="50%"
                      cy="90%"
                    >
                      <PolarAngleAxis
                        type="number"
                        domain={[0, 100]}
                        tick={false}
                      />
                      <RadialBar
                        dataKey="value"
                        background={{ fill: "#E6ECEE" }}
                        fill={probability >= 50 ? "#B04A57" : "#166C66"}
                        isAnimationActive={false}
                        cornerRadius={5}
                      />
                    </RadialBarChart>
                  </ResponsiveContainer>
                  <div className="gauge-value">
                    {result ? (
                      <>
                        {probability.toFixed(1)}
                        <span>%</span>
                      </>
                    ) : (
                      <span className="empty-number">—</span>
                    )}
                    <small>
                      {result ? "model probability" : "No result yet"}
                    </small>
                  </div>
                </div>
                <div className="gauge-scale">
                  <span>0%</span>
                  <span>100%</span>
                </div>
                <div className="estimate-note">
                  {result
                    ? `${probability >= 50 ? "Above" : "Below"} the model’s 50% classification threshold.`
                    : "Add measurements to see the estimate."}
                  <small>
                    Existing disease in the Cleveland cohort.
                    <br />
                    Not a ten-year cardiovascular risk score.
                  </small>
                </div>
              </article>
              <article className="panel contributors-panel">
                <h3>Key factors</h3>
                <p className="card-description">
                  How each measurement influences the estimate.
                </p>
                {result ? (
                  <>
                    <div
                      className="shap-chart"
                      style={{ height: showAll ? 395 : 220 }}
                    >
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={contributions}
                          layout="vertical"
                          margin={{ left: 0, right: 12, top: 10, bottom: 5 }}
                        >
                          <XAxis
                            type="number"
                            unit=" pp"
                            tick={{ fontSize: 10, fill: "#60757D" }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis
                            type="category"
                            dataKey="label"
                            width={122}
                            tick={{ fontSize: 11, fill: "#203238" }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <ReferenceLine x={0} stroke="#BAC8CC" />
                          <Tooltip
                            formatter={(v) => [
                              `${Number(v) > 0 ? "+" : ""}${v} percentage points`,
                              "Contribution",
                            ]}
                          />
                          <Bar
                            dataKey="points"
                            barSize={12}
                            radius={[2, 2, 2, 2]}
                            isAnimationActive={false}
                          >
                            {contributions.map((c) => (
                              <Cell
                                key={c.feature}
                                fill={c.points > 0 ? "#B04A57" : "#166C66"}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="chart-legend">
                      <span>
                        <i className="teal-dot" />
                        Lowers estimate
                      </span>
                      <span>
                        <i className="rose-dot" />
                        Raises estimate
                      </span>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => setShowAll(!showAll)}
                    >
                      {showAll ? "Show top six" : "View all factors"}
                    </button>
                    <details className="chart-data">
                      <summary>View detailed values</summary>
                      <ul>
                        {result.prediction.contributions.map((c) => (
                          <li key={c.feature}>
                            {labels[c.feature]}:{" "}
                            {(c.shap_value * 100).toFixed(2)} pp
                            {c.imputed ? " · imputed" : ""}
                          </li>
                        ))}
                      </ul>
                    </details>
                  </>
                ) : (
                  <div className="chart-empty">
                    <div className="empty-bars" aria-hidden="true">
                      {[38, 65, 46, 82, 27].map((w, i) => (
                        <span key={i} style={{ width: `${w}%` }} />
                      ))}
                    </div>
                    <p>
                      The most influential measurements
                      <br />
                      will appear here.
                    </p>
                  </div>
                )}
                <p className="chart-footnote">
                  Model explanations describe associations, not causes.
                </p>
              </article>
            </div>
            <article className="panel evidence-panel">
              <div className="evidence-title">
                <h3>Clinical evidence</h3>
                <span className="tag">2019 ACC/AHA guideline</span>
              </div>
              <p className="card-description">
                Relevant passages from the primary prevention guideline.
              </p>
              {result ? (
                <div className="evidence-list">
                  {result.evidence.map((e) => (
                    <section className="evidence-item" key={e.evidence_id}>
                      <div className="evidence-marker">{e.evidence_id}</div>
                      <div>
                        <p className="source-caption">
                          Executive Summary ·{" "}
                          {e.metadata.page
                            ? `page ${e.metadata.page_label || e.metadata.page}`
                            : `character ${e.metadata.start_index}`}
                        </p>
                        <blockquote>{e.text}</blockquote>
                        <a
                          href={e.metadata.source_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open original guideline <ExternalLink size={12} />
                        </a>
                      </div>
                    </section>
                  ))}
                </div>
              ) : (
                <div className="evidence-empty">
                  <FileText size={27} />
                  <div>
                    <strong>No evidence to display yet.</strong>
                    <p>Analyze a case to view related guideline passages.</p>
                  </div>
                </div>
              )}
              <div className="evidence-caution">
                <Info size={15} />
                <span>
                  Two passages may omit contraindications. Retrieval does not
                  establish treatment eligibility.
                </span>
              </div>
            </article>
            <article className="panel synthesis-panel">
              <h3>Summary</h3>
              {result?.synthesis.status === "complete" ? (
                <>
                  <p className="synthesis-text">{result.synthesis.text}</p>
                  <span className="source-caption">
                    AI-generated · clinician review required
                  </span>
                </>
              ) : (
                <div className="synthesis-empty">
                  <p>
                    {busy
                      ? "Preparing the assessment…"
                      : result
                        ? "A summary is currently unavailable. You can still review the estimate, key factors, and evidence above."
                        : "Your assessment summary will appear here."}
                  </p>
                </div>
              )}
            </article>
            <footer className="review-footer">
              <span>
                <FlaskConical size={13} /> Research prototype · not a diagnosis
              </span>
            </footer>
          </section>
        </div>
      </main>
    </>
  );
}
