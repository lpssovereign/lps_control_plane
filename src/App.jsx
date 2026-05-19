import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Archive,
  BookOpen,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileText,
  LineChart,
  MapPin,
  Printer,
  Rocket,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
} from "lucide-react";

const sites = [
  { site: "Central", adaTarget: 70, familyTarget: 30, actual: "TBD", note: "Largest proof site; mostly bilingual; Lalo averaged roughly 30–45 students." },
  { site: "Kearney", adaTarget: 80, familyTarget: 40, actual: "TBD", note: "High-school readiness / math-science bridge." },
  { site: "Lester", adaTarget: 140, familyTarget: 100, actual: "TBD", note: "High school continuation layer." },
  { site: "Rose Hill Elementary", adaTarget: 60, familyTarget: 25, actual: "TBD", note: "Elementary engagement / recruitment layer." },
];

const centralActivities = [
  ["Alka-Seltzer Rockets", "Successful", "Chemical reactions, prediction, measurement, iteration, visible outcomes."],
  ["Egg Drop Challenge", "Successful", "Engineering design, constraints, teamwork, failure analysis."],
  ["Spaghetti + Marshmallow Structures", "Successful", "Structural engineering, geometry, collaboration, stability."],
  ["Electronic Circuits", "Successful / needs materials", "Electricity, troubleshooting, sequencing, systems thinking."],
  ["Balloon Cars", "Productive failure", "Motion, force, redesign, materials, testing conditions."],
  ["Quest Rivals", "Prototype", "Student-informed alternative to passive Freckle-style math practice."],
];

const grantPipeline = ["Watch", "Discover", "Qualify", "Approve pursuit", "Parse requirements", "Gather evidence", "Draft", "Review", "Submit", "Implement", "Report", "Renew"];

const grantAgents = [
  ["Watcher Agent", "Scans CDE, GAINS, Grants.gov, funder pages, deadlines, RFAs, FAQs, and policy updates.", "Flags only. Human confirms relevance."],
  ["Qualifier Agent", "Scores eligibility, fit, deadline, award size, evidence readiness, staffing capacity, and compliance risk.", "Recommends Go / Maybe / No-Go. Human approves pursuit."],
  ["Requirement Parser", "Breaks RFAs or reporting surveys into questions, attachments, metrics, deadlines, owners, and evidence needs.", "Program lead validates the map."],
  ["Evidence Matcher", "Connects I/O forms, surveys, photos, parent nights, assessment exports, activity logs, and manuals to grant requirements.", "Suggested evidence must be reviewed."],
  ["Narrative Drafting", "Drafts needs statements, success stories, implementation narratives, continuation plans, and report answers.", "Drafts are never final without approval."],
  ["Compliance Review", "Flags overclaims, missing data, privacy risks, unsupported numbers, and identifiable student/family details.", "Human decides final wording."],
];

const performanceMeasures = [
  { area: "STEM Essential Skills / Enrichment", proof: "75% of student attendees improve critical thinking in math and science across school-year and summer programming.", data: "Student surveys, activity rubrics, staff observations, pre/post comparisons, and activity evidence.", rating: "Making Progress unless survey data proves the 75% threshold." },
  { area: "Student Attendance + Engagement", proof: "75% of student attendees increase school-day engagement by 50%, measured by teacher survey results.", data: "Teacher surveys, attendance/I-O forms, site notes, student surveys, and activity logs.", rating: "Data Not Available or Making Progress depending on teacher survey completion." },
  { area: "Family Engagement in STEM", proof: "Families participate in STEM-related engagement, parent nights, communication loops, and student recognition.", data: "Family sign-ins, parent/caregiver surveys, parent night records, communication logs, certificates, and artifacts.", rating: "Making Progress unless actual family target data is validated." },
  { area: "Mathematics Improvement", proof: "Students assessed twice demonstrate improvement in math or math-related STEM skills.", data: "STAR/IXL/Freckle/CMAS or district-approved assessment exports plus tutor/staff notes where assessment is unavailable.", rating: "Making Progress until official assessment exports are attached." },
];

const manualSections = [
  ["Timecard Reporting", "Document allowable program work accurately and consistently.", ["Approved direct programming", "Setup/breakdown", "Planning", "Parent communication", "Attendance documentation", "Approved admin duties"]],
  ["I/O Attendance Tracking", "Capture participation, dosage, arrival/departure, and site evidence.", ["Daily I/O form", "Student roster", "Meal count", "Transportation notes"]],
  ["Lesson Planning", "Make STEM/math enrichment executable without recreating curriculum daily.", ["Learning goal", "Materials", "Grade band", "Grouping model", "Safety", "Evidence"]],
  ["Surveys", "Convert handwritten surveys into grant-ready evidence.", ["Scan/photo", "Label by site/date/audience", "Transcribe", "Theme-code", "Summarize"]],
  ["Photo/Video Evidence", "Capture program evidence while protecting student privacy.", ["Permission status", "Activity tag", "De-identified media", "Review status"]],
  ["Parent Night + Family Engagement", "Document meaningful family participation and student recognition.", ["Sign-ins", "Meal plan", "Feedback", "Awards/certificates", "Follow-up"]],
];

const copyBlocks = [
  { title: "Central Elementary Site Narrative", text: "Central Elementary was my strongest implementation site. It was the largest site I supported and was mostly bilingual. I averaged approximately 30–45 students during the spring program window, beginning around April 1 and continuing through the end of programming around May 19. The site provided clear evidence that students responded well to hands-on STEM activities when materials were prepared, tasks were clear, and students were organized into smaller groups or stations." },
  { title: "Program Implementation Answer", text: "Program implementation at Central Elementary required daily preparation, materials coordination, student grouping, STEM activity delivery, behavior management, tutor coordination, and real-time adjustment. Activities were most effective when students had clear tasks, adequate materials, and station-based structures. When preparation or materials were incomplete, implementation became significantly more difficult." },
  { title: "Three Successes", text: "Three factors contributed to program success at Central Elementary: hands-on STEM activities generated strong student engagement; smaller groups and stations helped students stay on task; and consistent preparation with adequate materials made behavior and participation more manageable." },
  { title: "Three Challenges", text: "Three factors hindered implementation: spring sports and other activities competed with attendance; curriculum development often had to happen quickly; and behavior became difficult when materials, tasks, or transitions were not fully prepared." },
  { title: "Pilot Ask", text: "A recommended next step is to pilot a lightweight evidence-continuity workflow for A14 DISCOVER. The pilot would connect daily site logs, attendance, surveys, STEM activities, family engagement, photos, student work, and performance measures so grant reporting can be generated from evidence collected during the program instead of reconstructed manually at the end of the year." },
];

const fundingSources = [
  ["State OST Continuation", "Closest replacement or continuation lane for A14 DISCOVER-style OST programming.", "Attendance, family engagement, STEM activities, surveys, performance measures."],
  ["Youth Resiliency / Belonging", "Strong if framed around belonging, trusted adults, bilingual community relevance, and safe OST spaces.", "Student surveys, family surveys, staff reflections, belonging/engagement themes."],
  ["K–12 / Youth Development", "Possible for district/nonprofit partnerships around youth development, measurable outcomes, and sustainability.", "Outcomes, evaluation plan, leadership capacity, sustainability plan."],
  ["Corporate + Local Sponsors", "Fastest lane for STEM materials, circuits, rockets, robotics, badges, family-night supplies, and activity kits.", "Materials list, student reach, photos/artifacts, thank-you report."],
];

function classNames(...items) {
  return items.filter(Boolean).join(" ");
}

function SectionHeader({ kicker, title, children }) {
  return <div className="section-header"><p className="kicker">{kicker}</p><h2>{title}</h2>{children ? <p className="section-subtitle">{children}</p> : null}</div>;
}
function Badge({ children }) {
  return <span className="badge">{children}</span>;
}

function MetricCard({ icon: Icon, label, value, detail }) {
  return <motion.div className="card metric" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}><div className="metric-top"><div><p>{label}</p><strong>{value}</strong></div><span className="icon"><Icon size={22} /></span></div><small>{detail}</small></motion.div>;
}

function CopyBox({ title, text }) {
  const [copied, setCopied] = useState(false);
  return <div className="card copybox"><div className="copy-head"><h3>{title}</h3><button onClick={() => { navigator.clipboard?.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1200); }}>{copied ? "Copied" : "Copy"}</button></div><p>{text}</p></div>;
}

function QuestRivals() {
  return <div><SectionHeader kicker="Student-informed prototype" title="Quest Rivals — STEM Adventure Game">An early engagement prototype from Central Elementary student feedback: not a curriculum replacement, but a proof that academic review can become more interactive, competitive, and evidence-generating.</SectionHeader><div className="grid two"><div className="card dark"><p className="kicker">Prototype narrative</p><h3>Race. Type. Learn. Win.</h3><p>Quest Rivals turns math, science, typing, and STEM review into a two-player race with points, streaks, pets, hints, coins, shops, and subject worlds.</p></div><div className="card"><h3>Grant relevance</h3><div className="pill-list">{["STEM engagement", "Math/science practice", "Student voice", "Digital enrichment", "Attendance motivation", "Critical thinking"].map((x) => <Badge key={x}>{x}</Badge>)}</div></div></div><div className="grid three">{["Multi-subject world map", "Two-player competition", "Typing/race input loop", "Pets, hints, coins, shop", "Grade-banded question banks", "Freckle alternative concept"].map((x, i) => <div className="card" key={x}><h3>{x}</h3><p>{["Math, science, typing, history, coding, and engineering worlds.", "Score bars, turns, streaks, and visible win conditions.", "Students type answers and get immediate movement/feedback.", "Progression and reward loops students understand quickly.", "K–1, 2–3, and 4–5/6 differentiation model.", "Student-informed response to passive digital practice."][i]}</p></div>)}</div><CopyBox title="Quest Rivals Report Language" text="Students at Central Elementary expressed a need for more engaging alternatives to passive digital math practice. In response, we began prototyping a student-informed learning game called Quest Rivals, which turns academic review into a two-player STEM adventure using racing, typing, math/science questions, pets, hints, coins, and progression systems." /></div>;
}

function AltFunding() {
  return <div><SectionHeader kicker="Alternative funding strategy" title="Funding stack beyond CO-AAP">Diversify funding around OST continuation, STEM materials, youth resiliency, K–12 development, corporate sponsors, and future federal/state opportunities.</SectionHeader><div className="grid two">{fundingSources.map(([lane, fit, evidence]) => <div className="card" key={lane}><p className="kicker">{lane}</p><h3>{fit}</h3><p>{evidence}</p></div>)}</div><CopyBox title="Alternative Funding Narrative" text="Because CO-AAP funding may be uncertain, A14 DISCOVER should diversify its funding strategy rather than depend on a single grant stream. The strongest alternative funding package combines out-of-school-time continuation funding, STEM/materials sponsorships, youth belonging and resiliency grants, family engagement support, and a longer-term grant management workflow." /></div>;
}

function TrainingManual() {
  const [active, setActive] = useState(manualSections[0][0]);
  const current = manualSections.find((x) => x[0] === active) || manualSections[0];
  return <div><SectionHeader kicker="Operations handbook" title="A14 DISCOVER Site Coordinator Training Manual">The manual becomes an executable handbook: purpose, procedure, evidence, and grant-reporting connection.</SectionHeader><div className="split"><div className="side-list">{manualSections.map(([title, desc]) => <button key={title} onClick={() => setActive(title)} className={active === title ? "active" : ""}><strong>{title}</strong><small>{desc}</small></button>)}</div><div className="card"><p className="kicker">Manual section</p><h3>{current[0]}</h3><p>{current[1]}</p><div className="pill-list">{current[2].map((x) => <Badge key={x}>{x}</Badge>)}</div></div></div><CopyBox title="Manual-to-Grant Connection" text="The training manual supports CO-AAP reporting by standardizing how sites collect evidence. I/O forms support students served and attendance; lesson plans support STEM implementation; surveys support performance measures; parent night procedures support family engagement; photo/video processes support evidence documentation; and safety/incident procedures support implementation quality and compliance." /></div>;
}

function CentralCaseStudy() {
  return <div><SectionHeader kicker="Field evidence layer" title="Central Elementary case study">Central was the strongest proof site: largest site, mostly bilingual, roughly 30–45 students on average, and multiple hands-on STEM activities during the April 1–May 19 window.</SectionHeader><div className="grid four"><MetricCard icon={Users} label="Average daily group" value="30–45" detail="Approximate Central Elementary student range." /><MetricCard icon={CalendarDays} label="Implementation window" value="Apr 1–May 19" detail="Approximate spring implementation period." /><MetricCard icon={Rocket} label="STEM activities" value="6+" detail="Rockets, egg drop, circuits, structures, game prototype." /><MetricCard icon={MapPin} label="Site context" value="Bilingual" detail="Largest and mostly bilingual site." /></div><div className="grid three">{centralActivities.map(([title, result, detail]) => <div className="card" key={title}><p className="kicker">{result}</p><h3>{title}</h3><p>{detail}</p></div>)}</div></div>;
}

function DailyLog() {
  return <div><SectionHeader kicker="Daily site evidence" title="Generate the report as the program runs">Every day becomes a structured evidence record connected to STEM, attendance, family engagement, implementation, success stories, and challenges.</SectionHeader><div className="grid four">{["Date", "Site", "Student count", "Grade bands", "Activity", "Materials used", "Staff/tutors present", "Grouping model", "Engagement rating", "Behavior rating", "What worked", "What failed", "Photos/evidence", "Student work", "Grant tags", "Next-day adjustment"].map((x) => <div className="mini" key={x}>{x}</div>)}</div><CopyBox title="Daily Log Thesis" text="The grant report should not be reconstructed at the end of the year. It should be generated from daily site evidence while the program runs." /></div>;
}

function CopyCenter() {
  return <div><SectionHeader kicker="Copyable report language" title="Copy Center">Paste-ready blocks for CO-AAP, email, report, or presentation.</SectionHeader><div className="grid one">{copyBlocks.map((x) => <CopyBox key={x.title} {...x} />)}</div></div>;
}

function Performance() {
  return <div><SectionHeader kicker="State performance measures" title="One engine for every proof statement">Proof statement → rating → validation fields → data used → challenges → explanation.</SectionHeader><div className="grid two">{performanceMeasures.map((item) => <div className="card" key={item.area}><p className="kicker">Performance measure</p><h3>{item.area}</h3><p><strong>Proof:</strong> {item.proof}</p><p><strong>Data:</strong> {item.data}</p><p><strong>Likely rating:</strong> {item.rating}</p></div>)}</div></div>;
}

function Implementation() {
  return <div><SectionHeader kicker="Intervention implementation" title="Reusable Qualtrics response blocks">Strategy ratings, evidence-informed programs, digital math acceleration, staffing, dosage, stakeholders, success stories, challenges, and state measures.</SectionHeader><div className="grid two">{["Identify struggling students from assessments", "Notify parents/guardians", "Provide intervention strategies", "Publish curriculum/supplemental interventions", "Training/parent framework plans", "Digital math accelerated programs", "Staff recruitment/retention/growth", "Programming dosage hours/weeks"].map((x) => <div className="card" key={x}><h3>{x}</h3><p>Draft language, evidence source, missing data, and defensible rating should be attached here before final submission.</p></div>)}</div></div>;
}

function SurveyOps() {
  return <div><SectionHeader kicker="Handwritten survey processing" title="Paper surveys → grant-ready evidence">Collect, label, scan/photo, transcribe, code themes, aggregate, review, and export.</SectionHeader><div className="grid four">{["Collect + label", "Scan/photo", "Transcribe", "Theme-code", "Aggregate", "Review", "Export", "Archive"].map((x) => <div className="mini" key={x}>{x}</div>)}</div><div className="card table-card"><h3>CO-AAP targets captured</h3><table><thead><tr><th>Site</th><th>ADA Target</th><th>Family Target</th><th>Actual</th></tr></thead><tbody>{sites.map((s) => <tr key={s.site}><td>{s.site}</td><td>{s.adaTarget}</td><td>{s.familyTarget}</td><td>{s.actual}</td></tr>)}</tbody></table></div></div>;
}

function GrantOS() {
  return <div><SectionHeader kicker="Grant management app blueprint" title="GrantOS: watcher + qualifier + evidence-to-reporting engine">An ATS for grants: opportunity → qualification → requirements → evidence → draft → review → submit → implement → report → renew.</SectionHeader><div className="grid six">{grantPipeline.map((x, i) => <div className="mini" key={x}><strong>{i + 1}</strong><br />{x}</div>)}</div><div className="grid two">{grantAgents.map(([agent, job, gate]) => <div className="card" key={agent}><h3>{agent}</h3><p><strong>Job:</strong> {job}</p><p><strong>Gate:</strong> {gate}</p></div>)}</div><CopyBox title="GrantOS Pilot Language" text="The first pilot should not attempt to manage every district grant. It should start with one real workflow: CO-AAP end-of-year reporting for A14 DISCOVER. Once that workflow is proven, the same structure can expand into alternative funding, policy watchers, grant qualification, application drafting, evidence management, reporting, and renewals." /></div>;
}

const tabs = [
  ["game", "Quest Rivals", Sparkles], ["funding", "Alt Funding", Target], ["manual", "Training Manual", BookOpen],
  ["central", "Central Case Study", MapPin], ["daily", "Daily Log", CalendarDays], ["copy", "Copy Center", ClipboardList],
  ["performance", "Performance", LineChart], ["implementation", "Implementation", ShieldCheck], ["survey", "Survey Ops", FileText], ["grant", "Grant OS", BrainCircuit],
];

export default function App() {
  const [active, setActive] = useState("game");
  const content = useMemo(() => ({ game: <QuestRivals />, funding: <AltFunding />, manual: <TrainingManual />, central: <CentralCaseStudy />, daily: <DailyLog />, copy: <CopyCenter />, performance: <Performance />, implementation: <Implementation />, survey: <SurveyOps />, grant: <GrantOS /> }[active]), [active]);

  return (
    <div className="app">
      <header className="topbar no-print">
        <div>
          <p className="kicker">Education OS / A14 DISCOVER</p>
          <h1>CO-AAP End-of-Year Interactive Reporting Reader</h1>
        </div>
        <button className="print-btn" onClick={() => window.print()}><Printer size={16} /> Print / PDF</button>
      </header>

      <div className="layout">
        <aside className="sidebar no-print">
          {tabs.map(([id, label, Icon]) => (
            <button key={id} onClick={() => setActive(id)} className={classNames(active === id && "active")}><Icon size={17} /> {label}</button>
          ))}
          <div className="side-note"><strong>Demo note</strong><p>No private student data. This is a hosted workflow prototype for reporting, evidence, and pilot discussion.</p></div>
        </aside>

        <main className="main">
          <motion.div key={active} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            {content}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
