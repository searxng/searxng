;;; .dir-locals.el
;;
;; If you get ``*** EPC Error ***`` (even after a jedi:install-server) in your
;; emacs session, mostly you have jedi-mode enabled but the python enviroment is
;; missed.  The python environment has to be next to the
;; ``<repo>/.dir-locals.el`` in::
;;
;;     ./local/py3
;;
;; In Emacs, some buffer locals are referencing the project environment:
;;
;; - prj-root                                --> <repo>/
;; - python-environment-directory            --> <repo>/local
;; - python-environment-default-root-name    --> py3
;; - python-shell-virtualenv-root            --> <repo>/local/py3
;;       When this variable is set with the path of the virtualenv to use,
;;      `process-environment' and `exec-path' get proper values in order to run
;;      shells inside the specified virtualenv, example::
;;         (setq python-shell-virtualenv-root "/path/to/env/")
;;
;; To setup such an environment build target 'pyenv' or 'pyenvinstall'::
;;
;;   $ make pyenvinstall
;;
;; Alternatively create the virtualenv, source it and install jedi + epc
;; (required by `emacs-jedi <https://tkf.github.io/emacs-jedi>`_)::
;;
;;     $ python -m venv ./local/py3
;;     ...
;;     $ source ./local/py3/bin/activate
;;     (py3)$ # now install into the activated 'py3' environment ..
;;     (py3)$ pip install jedi epc
;;     ...
;;
;; Here is what also I found useful to add to my .emacs::
;;
;;     (global-set-key [f6] 'flycheck-mode)
;;     (add-hook 'python-mode-hook 'my:python-mode-hook)
;;
;;     (defun my:python-mode-hook ()
;;       (add-to-list 'company-backends 'company-jedi)
;;       (require 'jedi-core)
;;       (jedi:setup)
;;       (define-key python-mode-map (kbd "C-c C-d") 'jedi:show-doc)
;;       (define-key python-mode-map (kbd "M-.")     'jedi:goto-definition)
;;       (define-key python-mode-map (kbd "M-,")     'jedi:goto-definition-pop-marker)
;;     )
;;

((nil
  . ((fill-column . 80)
     (indent-tabs-mode . nil)
     ;; project root folder is where the `.dir-locals.el' is located
     (eval . (setq-local
	      prj-root (locate-dominating-file  default-directory ".dir-locals.el")))
     (eval . (setq-local
	      python-environment-directory (expand-file-name "./local" prj-root)))
     ;; use 'py3' enviroment as default
     (eval . (setq-local
	      python-environment-default-root-name "py3"))
     (eval . (setq-local
	      python-shell-virtualenv-root
              (expand-file-name python-environment-default-root-name python-environment-directory)
              ))
     (eval . (setq-local
	      python-shell-interpreter
	      (expand-file-name "bin/python" python-shell-virtualenv-root)))
     ))

 (makefile-gmake-mode
  . ((indent-tabs-mode . t)
     ))

 (yaml-mode
  . (
     ;; flycheck should use the local py3 environment
     (eval . (setq-local
	      flycheck-yaml-yamllint-executable
	      (expand-file-name "bin/yamllint" python-shell-virtualenv-root)))
     (eval . (setq-local
              flycheck-yamllintrc
              (expand-file-name  ".yamllint.yml" prj-root)))
     (flycheck-checker . yaml-yamllint)
     ))

 (python-mode
  . ((indent-tabs-mode . nil)

     (eval . (setq-local
	      python-environment-virtualenv
	      (list (expand-file-name "bin/virtualenv" python-shell-virtualenv-root)
		    ;;"--system-site-packages"
		    "--quiet")))

     (eval . (setq-local
	      pylint-command
	      (expand-file-name "bin/pylint" python-shell-virtualenv-root)))

     ;; pylint will find the '.pylintrc' file next to the CWD
     ;;   https://pylint.readthedocs.io/en/latest/user_guide/run.html#command-line-options
     (eval . (setq-local
	      flycheck-pylintrc ".pylintrc"))

     ;; flycheck & other python stuff should use the local py3 environment
     (eval . (setq-local
	      flycheck-python-pylint-executable python-shell-interpreter))

     ;; use 'M-x jedi:show-setup-info'  and 'M-x epc:controller' to inspect jedi server

     ;; https://tkf.github.io/emacs-jedi/latest/#jedi:environment-root -- You
     ;; can specify a full path instead of a name (relative path). In that case,
     ;; python-environment-directory is ignored and Python virtual environment
     ;; is created at the specified path.
     (eval . (setq-local  jedi:environment-root  python-shell-virtualenv-root))

     ;; https://tkf.github.io/emacs-jedi/latest/#jedi:server-command
     (eval .(setq-local
	     jedi:server-command
	     (list python-shell-interpreter
		   jedi:server-script)
	     ))

     ;; jedi:environment-virtualenv --> see above 'python-environment-virtualenv'
     ;; is set buffer local! No need to setup jedi:environment-virtualenv:
     ;;
     ;;    Virtualenv command to use.  A list of string.  If it is nil,
     ;;    python-environment-virtualenv is used instead.  You must set non-nil
     ;;    value to jedi:environment-root in order to make this setting work.
     ;;
     ;;    https://tkf.github.io/emacs-jedi/latest/#jedi:environment-virtualenv
     ;;
     ;; (eval . (setq-local
     ;; 	      jedi:environment-virtualenv
     ;; 	      (list (expand-file-name "bin/virtualenv" python-shell-virtualenv-root)
     ;; 		    ;;"--python"
     ;; 		    ;;"/usr/bin/python3.4"
     ;; 		    )))

     ;; jedi:server-args

     )))
