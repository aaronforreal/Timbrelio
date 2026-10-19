# Timbrelio

**CSC 475 / CSC 575 — DP3: Content-Based Visualization and Browsing of Sound Effects**

## 1. Project Overview

Timbrelio is an interactive system for browsing an audio collection by sound. It will extract audio features from the FMA Small dataset, estimate similarity between tracks, project the feature space into two dimensions, and display the result as a browsable map. Users will be able to filter the map, play audio, inspect clusters, and retrieve tracks that sound similar to a selected track.

The project investigates three questions:

1. How do conventional MIR features compare with a pretrained audio embedding for similarity retrieval?
2. How well do PCA and UMAP preserve useful neighbourhoods in a 2-D visualization?
3. Can users find related sounds through an interactive map without relying only on metadata?

The supplied datasets are music-centred rather than dedicated sound-effect collections. Timbrelio therefore treats each track as a general audio item and limits its conclusions to the tested music data.

## 2. Scope

### Core scope

- Process the 8,000 30-second excerpts in FMA Small.
- Extract conventional MIR features and one pretrained audio embedding.
- Compare PCA and UMAP projections.
- Compare k-means and HDBSCAN clustering.
- Build an interactive map with filtering, playback, item details, and five nearest neighbours.
- Evaluate neighbourhood quality, cluster quality, runtime, and basic usability.

### Stretch goal

If the core system is complete by November 20, test the final pipeline on a small, fixed subset of MTG-Jamendo. Music4All will be discussed as related work but will not be implemented during this project.

### Out of scope

- Training an audio representation model from scratch.
- Processing all of FMA, MTG-Jamendo, or Music4All.
- Production deployment or a streaming service.
- Approximate-nearest-neighbour indexing.
- A formal or large-scale user study.
- Personalized recommendation.

## 3. Requirements

| ID | Requirement | Completion criterion |
|---|---|---|
| R1 | Load and preprocess FMA Small | All valid tracks have aligned IDs, metadata, and standardized audio excerpts. |
| R2 | Extract features | Each valid track has conventional features and one learned embedding. |
| R3 | Create maps | Reproducible PCA and UMAP coordinates are saved for both representations. |
| R4 | Cluster tracks | K-means and HDBSCAN labels and evaluation metrics are recorded. |
| R5 | Retrieve similar tracks | Selecting a track returns five neighbours from the original feature space. |
| R6 | Browse interactively | Users can zoom, filter, select, inspect, and play tracks. |
| R7 | Reproduce results | Configuration, random seeds, package versions, and commands are documented. |

The cached application should respond to filtering and selection within two seconds on the development machine. Missing or corrupt files must be logged and skipped without stopping the pipeline. Dataset audio will not be committed to Git.

## 4. Datasets

### FMA Small — primary dataset

FMA contains audio, metadata, tags, a genre hierarchy, predefined splits, and precomputed features [8]. Timbrelio will use FMA Small: 8,000 balanced 30-second excerpts across eight top-level genres. This size is large enough for meaningful visualization while remaining practical before December 4. Genre labels will be used as imperfect reference labels for retrieval and clustering evaluation.

### MTG-Jamendo — optional stretch dataset

MTG-Jamendo contains more than 55,000 tracks with genre, instrument, and mood/theme tags [9]. Only a small reproducible subset will be considered, and only after the FMA system and evaluation are complete.

### Music4All — literature only

Music4All provides audio clips, metadata, genres, tags, and other information [10]. It is relevant to the project but is excluded from implementation because adding a third dataset would exceed the available schedule.

Raw audio will remain outside version control. A manifest will connect each item ID to its path, metadata, labels, and processing status. Derived features and coordinates will be cached locally.

## 5. Proposed Method

### 5.1 Preprocessing and features

Tracks will be decoded, converted to mono, resampled to a fixed rate, and checked for invalid or silent audio. Two representations will be created:

1. **Conventional features:** summary statistics for MFCCs, spectral centroid, bandwidth, roll-off, zero-crossing rate, RMS energy, chroma, tempo, and onset strength using librosa [11].
2. **Learned embedding:** one pretrained OpenL3 audio embedding, aggregated to one vector per track [12].

Features will be standardized before similarity, projection, and clustering.

### 5.2 Similarity, projection, and clustering

- Nearest neighbours will be computed in the original standardized feature space using cosine distance.
- PCA will provide a simple linear visualization baseline.
- UMAP will provide the main nonlinear map [13].
- K-means will provide the clustering baseline.
- HDBSCAN will test density-based clustering and allow tracks to remain unassigned [14].

The interface will not use 2-D map distance for retrieval because dimensionality reduction can distort similarity.

### 5.3 Interactive browser

The application will use Streamlit and Plotly with precomputed data. It will provide:

- an interactive 2-D scatter plot;
- colouring by genre or cluster;
- genre and cluster filters;
- hover and selected-track metadata;
- local audio playback;
- five nearest neighbours; and
- switching between saved feature and projection configurations.

```text
FMA Small
    |
    v
preprocessing -> feature extraction -> similarity / projection / clustering
                                             |
                                             v
                                      cached artefacts
                                             |
                                             v
                                  Streamlit + Plotly browser
```

## 6. Evaluation

| Component | Measures |
|---|---|
| Retrieval | Precision@5 and genre agreement among nearest neighbours |
| Projection | Trustworthiness, nearest-neighbour overlap, and runtime |
| Clustering | Silhouette score, adjusted Rand index, and HDBSCAN noise rate |
| Performance | Feature-extraction time, projection time, application load time, and interaction latency |
| Usability | Completion and comments from 4–6 classmates performing three short browsing tasks |

Genre is not a complete measure of perceived similarity. The report will therefore include several listening-based examples of useful and misleading neighbours.

The minimum successful result is a reproducible end-to-end FMA Small pipeline and a working browser with map navigation, filters, playback, and nearest neighbours. MTG-Jamendo is not required for project completion.

## 7. Tools

| Area | Tools |
|---|---|
| Language and analysis | Python, Jupyter, NumPy, pandas |
| Audio | librosa, soundfile, FFmpeg, OpenL3 |
| Modelling | scikit-learn, umap-learn, hdbscan |
| Application | Streamlit, Plotly |
| Testing and versioning | pytest, Git |
| Starting reference | Kadenze MIR clustering and visualization notebooks [19] |

## 8. Timeline

| Dates | Deliverable |
|---|---|
| Oct. 15–23 | Finalize design, assign roles, download FMA Small, and create the dataset manifest. |
| Oct. 24–30 | Complete preprocessing and conventional feature extraction. |
| Oct. 31–Nov. 6 | Implement PCA, UMAP, clustering, and nearest-neighbour retrieval. |
| Nov. 7–13 | Build the first complete interactive browser. |
| Nov. 14–20 | Add the learned embedding and compare both representations. |
| Nov. 21–27 | Complete evaluation, integration, testing, and optional MTG-Jamendo pilot. |
| Nov. 28–Dec. 4 | Fix defects, finalize the report and presentation, and prepare the demonstration. |

Core work takes priority over stretch goals. The team will review progress each week and drop the MTG-Jamendo pilot if any core requirement is incomplete on November 20.

## 9. Team Roles and Individual Objectives

## Nick Argument

**Role:** Dataset pipeline and conventional features

### Objective 1: Build the FMA data pipeline

- **PI1 (basic):** Load FMA Small audio and metadata with stable track IDs.
- **PI2 (basic):** Implement mono conversion, resampling, and invalid-file logging.
- **PI3 (expected):** Create a cached, resumable preprocessing pipeline.
- **PI4 (expected):** Report missing files, durations, sample rates, and genre counts.
- **PI5 (advanced):** Profile the complete pipeline and reduce unnecessary runtime or storage.

### Objective 2: Implement conventional MIR features

- **PI1 (basic):** Extract MFCC, spectral centroid, zero-crossing rate, and RMS statistics.
- **PI2 (basic):** Save feature vectors with correctly aligned track IDs.
- **PI3 (expected):** Add chroma, spectral contrast, roll-off, bandwidth, tempo, and onset features.
- **PI4 (expected):** Standardize features and inspect missing values, distributions, and correlations.
- **PI5 (advanced):** Compare a reduced feature set against the full set for retrieval quality and runtime.

## Aaron Sharma

**Role:** Interactive visualization and playback

### Objective 1: Build the interactive map

- **PI1 (basic):** Display saved 2-D coordinates in an interactive scatter plot.
- **PI2 (basic):** Add zoom, hover information, and genre or cluster colouring.
- **PI3 (expected):** Add genre, cluster, and representation filters.
- **PI4 (expected):** Add selected-track details and local audio playback.
- **PI5 (advanced):** Keep filtering and selection responsive across all 8,000 FMA Small tracks.

### Objective 2: Implement the browsing workflow

- **PI1 (basic):** Display five neighbours for a selected track.
- **PI2 (basic):** Allow the seed track and neighbours to be played from one view.
- **PI3 (expected):** Support switching between PCA and UMAP maps.
- **PI4 (expected):** Write and pilot three short browsing tasks with classmates.
- **PI5 (advanced):** Compare neighbour results between conventional and learned representations in the interface.

## GRADUATE_1_FIRST_NAME GRADUATE_1_LAST_NAME

**Role:** Learned representation and similarity evaluation

### Objective 1: Integrate and analyse a learned audio representation

- **PI1 (basic):** Integrate OpenL3 and document its input and aggregation settings.
- **PI2 (basic):** Verify alignment between learned embeddings, conventional features, and metadata.
- **PI3 (expected):** Compare both representations using Precision@5 and neighbourhood genre agreement.
- **PI4 (expected):** Test normalization, cosine distance, and PCA preprocessing under fixed conditions.
- **PI5 (advanced):** Analyse qualitative failure cases and recommend a final representation based on quality, runtime, and interpretability.

### Objective 2: Lead similarity experiments

- **PI1 (basic):** Define reproducible retrieval queries and evaluation scripts.
- **PI2 (basic):** Establish a random or genre-based comparison baseline.
- **PI3 (expected):** Measure retrieval performance by genre and identify weak categories.
- **PI4 (expected):** Measure embedding time, query time, memory use, and saved artefact size.
- **PI5 (advanced):** Run the optional MTG-Jamendo pilot if all FMA requirements are complete by November 20.

## Meet Shah 

**Role:** Projection, clustering, and system evaluation

### Objective 1: Evaluate projection and clustering methods

- **PI1 (basic):** Implement reproducible PCA and UMAP projections.
- **PI2 (basic):** Implement k-means and HDBSCAN clustering.
- **PI3 (expected):** Compare projections using trustworthiness, neighbour overlap, and runtime.
- **PI4 (expected):** Compare clusters using silhouette score, adjusted Rand index, and noise rate.
- **PI5 (advanced):** Test sensitivity to key UMAP and HDBSCAN parameters and justify the final configuration.

### Objective 2: Lead project-level evaluation and reporting

- **PI1 (basic):** Define experiment configurations, seeds, metric tables, and run naming.
- **PI2 (basic):** Select listening examples that show useful and misleading results.
- **PI3 (expected):** Design the three browsing tasks and summarize feedback from 4–6 classmates.
- **PI4 (expected):** Integrate retrieval, clustering, projection, timing, and usability findings into the report.
- **PI5 (advanced):** Document limitations and lead conversion of the final report to the required ISMIR LaTeX format.

- ## Hanif Muktadi

**Role:** Usability Testing, Feedback Analysis, and Evaluation Reporting

### Objective 1: Evaluate the Usability of the Interactive Browser

* **PI1 (basic):** Define three short browsing tasks to evaluate how users navigate the interactive audio map.
* **PI2 (basic):** Prepare clear testing instructions and record task completion, difficulties, and user feedback.
* **PI3 (expected):** Conduct usability tests with 4–6 classmates using the completed Timbrelio application.
* **PI4 (expected):** Analyze task completion rates, user comments, and common difficulties to identify usability issues.
* **PI5 (advanced):** Recommend interface improvements based on observed user difficulties and testing results.

### Objective 2: Analyze Results and Contribute to the Final Report

* **PI1 (basic):** Organize usability observations and feedback into structured tables.
* **PI2 (basic):** Summarize user experiences when browsing, filtering, selecting, and playing audio tracks.
* **PI3 (expected):** Create tables and visualizations to present usability findings clearly.
* **PI4 (expected):** Write the usability evaluation methodology, results, and limitations for the final report.
* **PI5 (advanced):** Integrate usability findings with the system's retrieval and visualization results to develop evidence-based recommendations for future improvements.


## 10. Related Work

Pampalk, Rauber, and Merkl organize music by psychoacoustic similarity and place related tracks near one another on a 2-D map [1]. The SOM-enhanced Jukebox [4] and later multi-view browsing work [5] connect collection structure with interactive exploration. MusicRainbow combines audio similarity with labels in a colour-coded interface [3]. Timbrelio adopts the same overview-and-browse principle with PCA, UMAP, playback, and nearest-neighbour inspection.

Khulusi et al. identify collection browsing as a major musical-data visualization task involving audio features, metadata, and interactive overviews [2]. Munzner's nested model informs how the problem, interaction design, and algorithms will be evaluated [7], while Shneiderman's overview-first pattern guides the map, filtering, and detail workflow [18]. Graph-based audio browsers [15, 16] and Sonixplorer's combined visualization and auralization approach [17] further show the value of linking visual exploration with listening.

Traditional MIR systems use engineered spectral, timbral, rhythmic, and harmonic descriptors [6]. OpenL3 provides general-purpose pretrained audio embeddings [12]. Timbrelio compares these approaches rather than assuming that the learned representation is better.

PCA provides a transparent linear baseline, while UMAP targets nonlinear neighbourhood preservation [13]. HDBSCAN supports variable-density clusters and noise points [14]. These methods will be evaluated quantitatively instead of selecting a map only because it looks visually separated.

FMA [8] supports the core experiment. MTG-Jamendo [9] and Music4All [10] show how the approach could later be evaluated on larger and more varied collections. The Kadenze notebooks provide the starting examples for clustering and visualization [19].

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Feature extraction takes too long | Cache each track, make processing resumable, and complete conventional features before OpenL3. |
| Labels do not represent perceived similarity | Treat genre as a proxy and report listening-based examples. |
| The map creates misleading distances | Retrieve neighbours from original features, not 2-D coordinates. |
| Application performance is poor | Load precomputed artefacts and avoid feature extraction during interaction. |
| Schedule slips | Prioritize FMA Small and drop the MTG-Jamendo stretch goal on November 20. |

## 12. Bibliography

[1] E. Pampalk, A. Rauber, and D. Merkl, “Content-based organization and visualization of music archives,” in *Proceedings of the 10th ACM International Conference on Multimedia*, pp. 570–579, 2002. [doi:10.1145/641007.641121](https://doi.org/10.1145/641007.641121)

[2] R. Khulusi, J. Kusnick, C. Meinecke, C. Gillmann, J. Focht, and S. Jänicke, “A survey on visualizations for musical data,” *Computer Graphics Forum*, vol. 39, no. 6, pp. 82–110, 2020. [doi:10.1111/cgf.13905](https://doi.org/10.1111/cgf.13905)

[3] E. Pampalk and M. Goto, “MusicRainbow: A new user interface to discover artists using audio-based similarity and web-based labeling,” in *Proceedings of ISMIR*, pp. 367–370, 2006. [PDF](https://staff.aist.go.jp/m.goto/MusicRainbow/pam_ismir06_music_rainbow.pdf)

[4] A. Rauber, E. Pampalk, and D. Merkl, “The SOM-enhanced JukeBox: Organization and visualization of music collections based on perceptual models,” *Journal of New Music Research*, vol. 32, no. 2, pp. 193–210, 2003. [doi:10.1076/jnmr.32.2.193.16738](https://doi.org/10.1076/jnmr.32.2.193.16738)

[5] E. Pampalk, S. Dixon, and G. Widmer, “Exploring music collections by browsing different views,” *Computer Music Journal*, vol. 28, no. 2, pp. 49–62, 2004. [doi:10.1162/014892604323112248](https://doi.org/10.1162/014892604323112248)

[6] G. Tzanetakis and P. Cook, “Musical genre classification of audio signals,” *IEEE Transactions on Speech and Audio Processing*, vol. 10, no. 5, pp. 293–302, 2002. [doi:10.1109/TSA.2002.800560](https://doi.org/10.1109/TSA.2002.800560)

[7] T. Munzner, “A nested model for visualization design and validation,” *IEEE Transactions on Visualization and Computer Graphics*, vol. 15, no. 6, pp. 921–928, 2009. [doi:10.1109/TVCG.2009.111](https://doi.org/10.1109/TVCG.2009.111)

[8] M. Defferrard, K. Benzi, P. Vandergheynst, and X. Bresson, “FMA: A dataset for music analysis,” in *Proceedings of ISMIR*, 2017. [Dataset](https://github.com/mdeff/fma)

[9] D. Bogdanov, M. Won, P. Tovstogan, A. Porter, and X. Serra, “The MTG-Jamendo dataset for automatic music tagging,” in *Machine Learning for Music Discovery Workshop, ICML*, 2019. [Dataset](https://mtg.github.io/mtg-jamendo-dataset/)

[10] I. A. P. Santana et al., “Music4All: A new music database and its applications,” in *2020 International Conference on Systems, Signals and Image Processing*, pp. 399–404, 2020. [doi:10.1109/IWSSIP48289.2020.9145170](https://doi.org/10.1109/IWSSIP48289.2020.9145170)

[11] B. McFee et al., “librosa: Audio and music signal analysis in Python,” in *Proceedings of the 14th Python in Science Conference*, pp. 18–25, 2015. [doi:10.25080/Majora-7b98e3ed-003](https://doi.org/10.25080/Majora-7b98e3ed-003)

[12] J. Cramer, H.-H. Wu, J. Salamon, and J. P. Bello, “Look, listen, and learn more: Design choices for deep audio embeddings,” in *IEEE ICASSP*, pp. 3852–3856, 2019. [doi:10.1109/ICASSP.2019.8682475](https://doi.org/10.1109/ICASSP.2019.8682475)

[13] L. McInnes, J. Healy, and J. Melville, “UMAP: Uniform manifold approximation and projection for dimension reduction,” 2018. [arXiv:1802.03426](https://arxiv.org/abs/1802.03426)

[14] R. J. G. B. Campello, D. Moulavi, and J. Sander, “Density-based clustering based on hierarchical density estimates,” in *Advances in Knowledge Discovery and Data Mining*, pp. 160–172, 2013. [doi:10.1007/978-3-642-37456-2_14](https://doi.org/10.1007/978-3-642-37456-2_14)

[15] C. Muelder, T. Provan, and K.-L. Ma, “Content based graph visualization of audio data for music library navigation,” in *IEEE International Symposium on Multimedia*, pp. 129–136, 2010. [doi:10.1109/ISM.2010.26](https://doi.org/10.1109/ISM.2010.26)

[16] J. Ono, D. C. Corrêa, M. D. Ferreira, R. F. Mello, and L. G. Nonato, “Similarity graph: Visual exploration of song collections,” in *SIBGRAPI*, pp. 253–260, 2015. [doi:10.1109/SIBGRAPI.2015.34](https://doi.org/10.1109/SIBGRAPI.2015.34)

[17] D. Lübbers, “Sonixplorer: Combining visualization and auralization for content-based exploration of music collections,” in *Proceedings of ISMIR*, pp. 590–593, 2005. [PDF](https://ismir2005.ismir.net/proceedings/1025.pdf)

[18] B. Shneiderman, “The eyes have it: A task by data type taxonomy for information visualizations,” in *Proceedings of the IEEE Symposium on Visual Languages*, pp. 336–343, 1996. [doi:10.1109/VL.1996.545307](https://doi.org/10.1109/VL.1996.545307)

[19] G. Tzanetakis, “MIR Program Kadenze: Course 2, Session 6 — clustering and visualization notebooks,” GitHub. [Repository](https://github.com/gtzan/mir_program_kadenze/tree/master/course2/session6)
