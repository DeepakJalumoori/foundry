import pytest
from pydantic import ValidationError

from app.schemas.candidate_profile import (
    BasicInfo,
    CertificationOrAchievementItem,
    EducationItem,
    EvidenceItem,
    SkillItem,
    StructuredCandidateProfile,
    WorkExperienceItem,
)
from app.services.profile_validator import validate_and_ground_profile
from app.services.resume_extractor import ExtractedPage, ResumeExtractionResult


def _sample_extraction(text: str) -> ResumeExtractionResult:
    return ResumeExtractionResult(
        extracted_text=f"[Page 1]\n{text}",
        page_count=1,
        pages=[ExtractedPage(page_number=1, text=text)],
        status="extracted",
        warnings=[],
    )


def test_valid_structured_profile_and_missing_optional_fields() -> None:
    profile = StructuredCandidateProfile(
        basic_info=BasicInfo(full_name="Jordan Lee"),
        skills=[
            SkillItem(
                name="Python",
                category="programming_languages",
                evidence_snippet="Built services in Python",
                page_number=1,
            )
        ],
    )
    assert profile.basic_info.years_of_experience is None
    assert profile.work_experience == []
    assert profile.education == []


def test_invalid_data_types_rejected_by_pydantic() -> None:
    with pytest.raises(ValidationError):
        StructuredCandidateProfile.model_validate(
            {
                "basic_info": {"years_of_experience": "ten years"},
            }
        )


def test_malformed_llm_json_rejected_by_pydantic() -> None:
    with pytest.raises(ValidationError):
        StructuredCandidateProfile.model_validate_json("{not valid json")


def test_deduplicates_skills_by_case_without_merging_distinct_tech() -> None:
    resume_text = "Skills: Python, FastAPI, React, React Native"
    profile = StructuredCandidateProfile(
        skills=[
            SkillItem(name="Python", category="programming_languages", evidence_snippet="Skills: Python", page_number=1),
            SkillItem(name=" python ", category="programming_languages", evidence_snippet="Skills: Python", page_number=1),
            SkillItem(name="React", category="frameworks", evidence_snippet="React, React Native", page_number=1),
            SkillItem(name="React Native", category="frameworks", evidence_snippet="React, React Native", page_number=1),
        ]
    )

    outcome = validate_and_ground_profile(profile, _sample_extraction(resume_text))
    assert [s.name for s in outcome.profile.skills] == ["Python", "React", "React Native"]
    assert outcome.extraction_status == "extracted_with_warnings"
    assert any("Duplicate skill" in w for w in outcome.warnings)


def test_invalid_dates_and_inconsistent_current_end_date_flagged() -> None:
    resume_text = "Acme Corp Engineer 2023-05 to 2021-01\nBeta Inc Lead 2024-01 to 2024-06"
    profile = StructuredCandidateProfile(
        work_experience=[
            WorkExperienceItem(
                organization="Acme Corp",
                job_title="Engineer",
                start_date="2023-05",
                end_date="2021-01",
                evidence_snippet="Acme Corp Engineer 2023-05 to 2021-01",
                page_number=1,
            ),
            WorkExperienceItem(
                organization="Beta Inc",
                job_title="Lead",
                start_date="2024-01",
                end_date="2024-06",
                is_current=True,
                evidence_snippet="Beta Inc Lead 2024-01 to 2024-06",
                page_number=1,
            ),
            WorkExperienceItem(
                organization="Gamma LLC",
                job_title="Intern",
                start_date="not-a-date",
                evidence_snippet="Acme Corp",
                page_number=1,
            ),
        ],
        education=[
            EducationItem(
                institution="State Univ",
                start_date="2022",
                end_date="2020",
                evidence_snippet="Acme Corp",
                page_number=1,
            )
        ],
    )

    outcome = validate_and_ground_profile(profile, _sample_extraction(resume_text))
    assert outcome.extraction_status == "requires_manual_review"
    assert all(exp.evidence_status == "requires_review" for exp in outcome.profile.work_experience)
    assert outcome.profile.education[0].evidence_status == "requires_review"


def test_missing_and_ungrounded_evidence_flagged_for_review() -> None:
    resume_text = "Jordan Lee\nBackend Developer with Python"
    profile = StructuredCandidateProfile(
        skills=[
            SkillItem(
                name="Rust",
                category="programming_languages",
                evidence_snippet="10 years of Rust kernel development",
                page_number=1,
            )
        ],
        evidence=[
            EvidenceItem(
                claim="PhD in Quantum Computing",
                snippet=None,
                page_number=1,
                confidence=0.99,
            )
        ],
    )

    outcome = validate_and_ground_profile(profile, _sample_extraction(resume_text))
    assert outcome.extraction_status == "requires_manual_review"
    assert outcome.profile.skills[0].evidence_status == "requires_review"
    assert outcome.profile.evidence[0].status == "requires_review"
    assert outcome.profile.evidence[0].confidence is None


def test_grounded_and_ungrounded_certifications_and_achievements() -> None:
    resume_text = (
        "Certifications: AWS Certified Solutions Architect - Associate (2024)\n"
        "Achievements: Winner of FinTech Hackathon 2023"
    )
    profile = StructuredCandidateProfile(
        certifications_and_achievements=[
            CertificationOrAchievementItem(
                title="AWS Certified Solutions Architect",
                issuer="AWS",
                date="2024",
                evidence_snippet="AWS Certified Solutions Architect - Associate (2024)",
                page_number=1,
            ),
            CertificationOrAchievementItem(
                title="Google Cloud Professional Architect",
                issuer="Google",
                evidence_snippet="Google Cloud Professional Architect",
                page_number=1,
            ),
            CertificationOrAchievementItem(
                title="Winner of FinTech Hackathon 2023",
                evidence_snippet="Winner of FinTech Hackathon 2023",
                page_number=1,
            ),
            CertificationOrAchievementItem(
                title="Forbes 30 Under 30",
                evidence_snippet=None,
                page_number=1,
            ),
        ]
    )

    outcome = validate_and_ground_profile(profile, _sample_extraction(resume_text))
    assert outcome.extraction_status == "extracted_with_warnings"
    certs = outcome.profile.certifications_and_achievements
    assert certs[0].evidence_status == "explicitly_stated"
    assert certs[1].evidence_status == "requires_review"
    assert certs[2].evidence_status == "explicitly_stated"
    assert certs[3].evidence_status == "requires_review"


def test_short_snippet_grounding_prevents_substring_false_positives() -> None:
    # "Google" contains "go" and "React" contains "r", but standalone Go/R are absent
    google_only_text = "Software Engineer at Google working on React."
    profile_false_pos = StructuredCandidateProfile(
        skills=[
            SkillItem(name="Go", category="programming_languages", evidence_snippet="Go", page_number=1),
            SkillItem(name="R", category="programming_languages", evidence_snippet="R", page_number=1),
        ]
    )
    outcome_false = validate_and_ground_profile(profile_false_pos, _sample_extraction(google_only_text))
    assert outcome_false.extraction_status == "requires_manual_review"
    assert outcome_false.profile.skills[0].evidence_status == "requires_review"
    assert outcome_false.profile.skills[1].evidence_status == "requires_review"

    # Standalone Go, R, and C++ with whitespace/line-break normalization
    standalone_text = "Languages:\n  Go,   R,\n  C++, and Python"
    profile_true_pos = StructuredCandidateProfile(
        skills=[
            SkillItem(name="Go", category="programming_languages", evidence_snippet="Go", page_number=1),
            SkillItem(name="R", category="programming_languages", evidence_snippet="R", page_number=1),
            SkillItem(name="C++", category="programming_languages", evidence_snippet="C++", page_number=1),
            SkillItem(
                name="Python",
                category="programming_languages",
                evidence_snippet="Go, R, C++, and Python",
                page_number=1,
            ),
        ]
    )
    outcome_true = validate_and_ground_profile(profile_true_pos, _sample_extraction(standalone_text))
    assert outcome_true.extraction_status == "extracted"
    assert all(s.evidence_status == "explicitly_stated" for s in outcome_true.profile.skills)
