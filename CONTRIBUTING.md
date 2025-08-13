# Contributing to The Commons

Thank you for your interest in contributing to The Commons!  
This project is an evolving experiment, and we welcome contributors of all skill levels.

---

## 👣 Contribution Philosophy

We treat pull requests as conversation tools, not just merge candidates.

- **Draft PRs are encouraged**: If something breaks or behaves unexpectedly, open a draft PR to surface it.
- **Don’t worry about “perfect”**: Flagging issues early is more useful than trying to fix everything at once.
- **All changes are reviewed** before merging—this is intentional to avoid accidental breakage during early development.
- **Use the `#start-here` channel in Discord** for any uncertainty—ask, share context, or pair up.

---

## 🔁 Pull Request Expectations

- **Testing first**: Pull the branch locally, run `docker compose up`, and confirm the PR does what it claims.
- **Mark it clearly**:
  - Use “Draft” if it's exploratory or in progress
  - Use descriptive titles and short commit messages
- **No auto-merging**: All merges go through manual verification for now
- **If it’s broken code on purpose (e.g. to show something)**, write that in the PR description

---

If you’re unsure where to start, check the `#start-here` channel in our Discord or open an issue. We’re happy to help you get involved.

For a full project overview, see [README.md](README.md) and [docs/architecture.md](docs/architecture.md).

## Working with Labels

### Quick-Start Checklist

When working with the label system:

- [ ] **Enable labels**: Set `LABELS_ENABLED=true` (backend) and `VITE_LABELS_ENABLED=true` (frontend)
- [ ] **Seed data**: Run `python backend/scripts/seed_labels.py` for default labels
- [ ] **Test flows**: Verify label creation, assignment, filtering, and delegation
- [ ] **Check performance**: Test with stress data using `make seed-stress`
- [ ] **Validate UX**: Ensure label components work across all pages

### Key Resources

- 📖 [Labels Overview](docs/labels_overview.md) - Philosophy and data model
- 🛠️ [Labels Playbook](docs/labels_playbook.md) - Practical implementation guide
- 🧪 [Label System Validation](docs/label_system_validation.md) - Testing procedures

### Common Patterns

```typescript
// Frontend: Filter by label
const polls = await listPolls({ label: 'mobility' });

// Backend: Create poll with labels
poll_data = { title: "...", labels: ["mobility", "education"] }

// API: Set label-specific delegation
await setDelegation("username", "mobility");
```

---

## Development Setup
... *(Keep the steps as they are)*

## Development Workflow
... *(Keep as is)*

## Coding Standards
... *(Keep as is)*

## Logging and Audit Trails
... *(Keep as is)*

## Testing
... *(Keep as is)*

## API Development
... *(Keep as is)*

## Pull Request Process
... *(Keep as is)*

## Code Review Guidelines
... *(Keep as is)*

## Release Process
... *(Keep as is)*

---

## Getting Help

- Open an issue for bugs  
- Use discussions for questions  
- Join our community chat: [your-discord-invite-link]  
- Check existing documentation  

---

## License

By contributing to The Commons, you agree that your contributions will be licensed under the project's MIT License.