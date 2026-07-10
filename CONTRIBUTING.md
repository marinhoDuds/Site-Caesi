# Contributing

Recommendations for contributing to this project.

## Code Style
Write code that is clear, maintainable, and easy to review.
Use docstrings on [PEP 257](https://peps.python.org/pep-0257/) pattern for public classes, functions, and methods. An example is given bellow:

```python
class User:
    """Represent a user of the system.

    Attributes
    ----------
    name : str
        The user's name.
    email : str
        The user's email address.
    """

    def __init__(self, name: str, email: str) -> None:
        """Initialize a new user.

        Parameters
        ----------
        name : str
            The user's name.
        email : str
            The user's email address.
        """

        self.name = name
        self.email = email

    def get_contact(self, include_email: bool = True) -> str:
        """Return a formatted contact string.

        Parameters
        ----------
        include_email : bool, optional
            If True, include the email address in the returned string.

        Returns
        -------
        str
            A string with the user's contact information.

        Raises
        ------
        ValueError
            If the user's name is empty.
        """

        if not self.name:
            raise ValueError("name cannot be empty")

        if include_email:
            return f"{self.name} <{self.email}>"

        return self.name

```

## Git Style

### Branch Conventions
Use conventional branch naming:

- `main`: Main production branch.
- `homolog`: Pre-production branch before `main`.
- `feature/<name>`: New features, usually branched from `homolog`.
- `release/<version>`: Release preparation branch, merged back into `homolog` and `main`.
- `hotfix/<name>`: Urgent fix branch for production issues.

### Commit Conventions

Use conventional commit prefixes:

- `feat:` Backward-compatible features.
- `fix:` Bug fixes.
- `chore:` Maintenance and repository housekeeping.
- `refactor:` Internal code changes without behavior changes.
- `test:` New or updated tests.
- `ci:` Workflow and pipeline changes.
- `docs:` Documentation updates.
- `build:` Packaging and release metadata.

#### Breaking changes

Use `!` in the subject (for example, `feat!:`) or add a `BREAKING CHANGE:` footer when a change is not backward-compatible.

#### Practical commit rules

- Keep each commit focused on one logical change.
- Prefer small, reviewable commits over large mixed commits.
- Keep `main` releasable, since release automation reads from that branch.

### Main Branch Stability

Recommended protection rules for `main`:

- Require CI workflows to pass before merge.
- Require at least one pull request review.
- Block direct pushes, except emergency maintenance.
- Merge only commits that follow the conventions above.
- Merge into `main` only from `homolog`.